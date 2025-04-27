import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

from core.agent import PenTestAgent
from network.environment.setup import Environment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EnvRunner")

class EnvironmentRunner:
    """
    Orchestrates the execution of penetration testing agents across multiple environments.
    Handles environment setup, agent execution, and performance tracking.
    """
    
    def __init__(self, 
                 base_image_path: str = "/home/nitu/noble_base.qcow2",
                 ssh_user: str = "root", 
                 ssh_password: str = "ubuntu",
                 environments_dir: str = "network/sample_env",
                 results_dir: str = "results"):
        """
        Initialize the environment runner.
        
        Args:
            base_image_path: Path to base VM image
            ssh_user: SSH username for VMs
            ssh_password: SSH password for VMs
            environments_dir: Directory containing environment setup scripts
            results_dir: Directory to store results
        """
        self.base_image_path = os.path.expanduser(base_image_path)
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.environments_dir = environments_dir
        self.results_dir = results_dir
        
        # Create results directory if it doesn't exist
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Track statistics
        self.stats = {
            "total_flags": 0,
            "environments_completed": 0,
            "environments_failed": 0,
            "total_time": 0
        }
        
        # Detailed results for each environment
        self.environment_results = {}
        
    def discover_environments(self) -> List[str]:
        """
        Discover available environment configurations.
        
        Returns:
            List of environment directory names
        """
        environments = []
        for item in os.listdir(self.environments_dir):
            full_path = os.path.join(self.environments_dir, item)
            if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "1.sh")):
                environments.append(item)
        
        logger.info(f"Discovered {len(environments)} environments: {environments}")
        return sorted(environments)
        
    def setup_environment(self, env_name: str) -> bool:
        """
        Set up a particular environment.
        
        Args:
            env_name: Name of the environment to set up
            
        Returns:
            True if setup was successful, False otherwise
        """
        logger.info(f"Setting up environment: {env_name}")
        scripts_dir = os.path.join(self.environments_dir, env_name)
        
        env_setup = Environment(
            base_image=self.base_image_path,
            ssh_user=self.ssh_user,
            ssh_password=self.ssh_password,
            scripts_dir=scripts_dir,
            rebuild=True  # Always rebuild to ensure clean environment
        )
        
        success = env_setup.setup_environment()
        if success:
            logger.info(f"Environment {env_name} setup completed successfully")
        else:
            logger.error(f"Environment {env_name} setup failed")
        
        return success
        
    def run_agent_on_environment(self, env_name: str) -> Dict:
        """
        Run the penetration testing agent on a specific environment.
        
        Args:
            env_name: Name of the environment to test
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"Starting agent on environment: {env_name}")
        
        start_time = time.time()
        
        # Create and run the agent
        agent = PenTestAgent()
        agent.run()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Collect results
        results = {
            "environment": env_name,
            "flags_found": len(agent.flags),
            "execution_time": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update statistics
        self.stats["total_flags"] += results["flags_found"]
        self.stats["total_time"] += duration
        
        if results["flags_found"] > 0:
            self.stats["environments_completed"] += 1
        else:
            self.stats["environments_failed"] += 1
        
        # Save environment result
        self.environment_results[env_name] = results
        
        # Log results
        logger.info(f"Environment {env_name} completed in {duration:.2f} seconds")
        logger.info(f"Flags found: {results['flags_found']}")
        
        return results
        
    def save_results(self) -> None:
        """
        Save test results to a file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"results_{timestamp}.json")
        
        output = {
            "summary": self.stats,
            "environments": self.environment_results,
            "timestamp": datetime.now().isoformat()
        }
        
        import json
        with open(results_file, 'w') as f:
            json.dump(output, f, indent=4)
            
        logger.info(f"Results saved to {results_file}")
    
    def save_results_to_csv(self) -> None:
        """
        Save test results to CSV files - one for summary and one for detailed environment results.
        Also includes a separate time per environment analysis CSV.
        """
        import csv
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary results
        summary_file = os.path.join(self.results_dir, f"summary_{timestamp}.csv")
        with open(summary_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Total Environments', 'Completed', 'Failed', 'Total Flags', 'Total Time (s)'])
            writer.writerow([
                self.stats["environments_completed"] + self.stats["environments_failed"],
                self.stats["environments_completed"],
                self.stats["environments_failed"],
                self.stats["total_flags"],
                f"{self.stats['total_time']:.2f}"
            ])
        
        # Save detailed environment results
        details_file = os.path.join(self.results_dir, f"environment_details_{timestamp}.csv")
        with open(details_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Environment', 'Flags Found', 'Execution Time (s)', 'Timestamp'])
            
            for env_name, results in self.environment_results.items():
                writer.writerow([
                    env_name,
                    results["flags_found"],
                    f"{results['execution_time']:.2f}",
                    results["timestamp"]
                ])
        
        # Save time per environment analysis
        time_analysis_file = os.path.join(self.results_dir, f"time_analysis_{timestamp}.csv")
        with open(time_analysis_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Environment', 'Execution Time (s)', 'Flags Found', 'Time per Flag (s)', 'Success Rate'])
            
            for env_name, results in self.environment_results.items():
                execution_time = results["execution_time"]
                flags_found = results["flags_found"]
                
                # Calculate time per flag (handle division by zero)
                time_per_flag = execution_time / flags_found if flags_found > 0 else float('inf')
                time_per_flag_str = f"{time_per_flag:.2f}" if flags_found > 0 else "N/A"
                
                # Calculate success rate (1 if found flags, 0 if not)
                success_rate = 1 if flags_found > 0 else 0
                
                writer.writerow([
                    env_name,
                    f"{execution_time:.2f}",
                    flags_found,
                    time_per_flag_str,
                    success_rate
                ])
        
        logger.info(f"Summary results saved to {summary_file}")
        logger.info(f"Detailed environment results saved to {details_file}")
        logger.info(f"Time analysis saved to {time_analysis_file}")
            
    def run_all_environments(self) -> Dict:
        """
        Run the penetration testing agent on all available environments.
        
        Returns:
            Dictionary with test results summary
        """
        environments = self.discover_environments()
        
        for env_name in environments:
            try:
                logger.info(f"=== Starting environment: {env_name} ===")
                
                # Set up the environment
                # if not self.setup_environment(env_name):
                #     logger.error(f"Skipping environment {env_name} due to setup failure")
                #     self.stats["environments_failed"] += 1
                #     continue
                
                # Run the agent
                self.run_agent_on_environment(env_name)
                
            except Exception as e:
                logger.error(f"Error processing environment {env_name}: {str(e)}", exc_info=True)
                self.stats["environments_failed"] += 1
                
        # Save final results
        self.save_results()
        
        return self.stats
        
    def run_specific_environment(self, env_name: str) -> Optional[Dict]:
        """
        Run the penetration testing agent on a specific environment.
        
        Args:
            env_name: Name of the environment to test
            
        Returns:
            Dictionary with test results or None if setup failed
        """
        try:
            logger.info(f"=== Starting environment: {env_name} ===")
            
            # Set up the environment
            # if not self.setup_environment(env_name):
            #     logger.error(f"Skipping environment {env_name} due to setup failure")
            #     self.stats["environments_failed"] += 1
            #     return None
            
            # Run the agent
            results = self.run_agent_on_environment(env_name)
            
            # Save results
            self.save_results()
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing environment {env_name}: {str(e)}", exc_info=True)
            self.stats["environments_failed"] += 1
            return None

def main():
    """
    Main entry point for the environment runner.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run penetration testing agent on environments')
    parser.add_argument('--env', type=str, help='Specific environment to run', default=None)
    parser.add_argument('--base-image', type=str, help='Path to base VM image', 
                        default="/home/nitu/noble_base.qcow2")
    parser.add_argument('--ssh-user', type=str, help='SSH username for VMs', default="root")
    parser.add_argument('--ssh-password', type=str, help='SSH password for VMs', default="ubuntu")
    
    args = parser.parse_args()
    
    runner = EnvironmentRunner(
        base_image_path=args.base_image,
        ssh_user=args.ssh_user,
        ssh_password=args.ssh_password
    )
    
    if args.env:
        # Run a specific environment
        runner.run_specific_environment(args.env)
    else:
        # Run all environments
        runner.run_all_environments()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Total environments tested: {runner.stats['environments_completed'] + runner.stats['environments_failed']}")
    print(f"Environments completed successfully: {runner.stats['environments_completed']}")
    print(f"Environments failed: {runner.stats['environments_failed']}")
    print(f"Total flags found: {runner.stats['total_flags']}")
    print(f"Total execution time: {runner.stats['total_time']:.2f} seconds")
    

if __name__ == "__main__":
    main()