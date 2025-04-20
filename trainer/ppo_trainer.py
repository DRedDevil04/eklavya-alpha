from transformers import PreTrainedModel, PreTrainedTokenizer
from trl import PPOTrainer, PPOConfig


class RLHFTrainer:
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, device: str = "cpu"):
        self.tokenizer = tokenizer
        self.model = model

        config = PPOConfig(
            model_name=None,  # Not needed since we're passing the model directly
            learning_rate=1e-5,
            batch_size=2,
            mini_batch_size=1,
            log_with=None,
            remove_unused_columns=False
        )

        self.trainer = PPOTrainer(config, self.model, self.tokenizer)

    def generate_response(self, prompt: str, max_new_tokens: int = 50) -> str:
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.model.device)
        output_ids = self.model.generate(input_ids=input_ids, max_new_tokens=max_new_tokens)
        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return response.strip()

    def train_on_single_step(self, prompt: str, response: str, reward: float):
        """
        Train the LLM using PPO on a single (prompt, response, reward) triplet.
        """
        self.trainer.step([prompt], [response], [reward])
        print(f"[RLHFTrainer] Updated model with reward: {reward}")
