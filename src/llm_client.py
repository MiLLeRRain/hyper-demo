"""
Unified LLM Client with Switchable Providers
Supports: DeepSeek Official, Qwen Official, OpenRouter
All providers use OpenAI-compatible API format
"""

import yaml
from openai import OpenAI
from typing import Optional, Dict, Any
import os


class LLMClient:
    """
    统一的LLM客户端 - 支持随时切换提供商

    所有提供商使用相同的OpenAI兼容API格式，只需更改:
    1. base_url (API端点)
    2. api_key (认证密钥)
    3. model (模型名称)
    """

    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化LLM客户端

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.client = self._create_client()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"配置文件未找到: {config_path}\n"
                f"请复制 config.example.yaml 为 config.yaml 并填写API密钥"
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 验证配置
        active_provider = config.get('active_provider')
        if not active_provider:
            raise ValueError("配置文件缺少 'active_provider'")

        if active_provider not in config.get('providers', {}):
            raise ValueError(f"未知的提供商: {active_provider}")

        return config

    def _create_client(self) -> OpenAI:
        """
        创建OpenAI客户端

        所有提供商使用相同的OpenAI SDK，只需更改base_url和api_key
        """
        active_provider = self.config['active_provider']
        provider_config = self.config['providers'][active_provider]

        # 验证API密钥
        api_key = provider_config.get('api_key', '')
        if not api_key or api_key.startswith('YOUR_'):
            raise ValueError(
                f"请在 config.yaml 中设置 {active_provider} 的 API 密钥"
            )

        # 创建客户端 - 所有提供商使用相同的方式
        client = OpenAI(
            api_key=api_key,
            base_url=provider_config['base_url']
        )

        print(f"✓ 已连接到提供商: {active_provider}")
        print(f"  - 端点: {provider_config['base_url']}")

        return client

    def _get_model_name(self) -> str:
        """获取当前模型名称"""
        active_provider = self.config['active_provider']
        provider_config = self.config['providers'][active_provider]

        # OpenRouter有多个模型可选
        if active_provider == 'openrouter':
            # 默认使用DeepSeek，可以通过配置切换
            model_choice = provider_config.get('active_model', 'deepseek')
            return provider_config['models'][model_choice]
        else:
            return provider_config['model']

    def generate_decision(self, prompt: str, temperature: float = 0.3) -> str:
        """
        生成AI交易决策

        Args:
            prompt: NoF1.ai格式的提示词 (11,053字符)
            temperature: 温度参数，越低越确定性 (0-1)

        Returns:
            AI模型的决策文本
        """
        try:
            model_name = self._get_model_name()

            # 所有提供商使用相同的API调用方式
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000  # 足够输出完整决策
            )

            # 提取响应文本
            decision = response.choices[0].message.content

            # 记录使用情况
            usage = response.usage
            print(f"✓ AI决策完成 (模型: {model_name})")
            print(f"  - 输入tokens: {usage.prompt_tokens}")
            print(f"  - 输出tokens: {usage.completion_tokens}")
            print(f"  - 总计tokens: {usage.total_tokens}")

            return decision

        except Exception as e:
            print(f"✗ AI决策失败: {e}")
            raise

    def switch_provider(self, new_provider: str):
        """
        运行时切换提供商

        Args:
            new_provider: 'deepseek_official' | 'qwen_official' | 'openrouter'
        """
        if new_provider not in self.config['providers']:
            raise ValueError(f"未知的提供商: {new_provider}")

        print(f"正在切换提供商: {self.config['active_provider']} -> {new_provider}")

        self.config['active_provider'] = new_provider
        self.client = self._create_client()

        print(f"✓ 已切换到: {new_provider}")

    def get_current_provider(self) -> str:
        """返回当前使用的提供商"""
        return self.config['active_provider']


# 使用示例
if __name__ == '__main__':
    # 初始化客户端 (使用config.yaml中的active_provider)
    client = LLMClient('config.yaml')

    # 模拟NoF1.ai格式的提示词
    test_prompt = """
You are managing a cryptocurrency portfolio with the following positions:

**Current Holdings:**
- BTC: Long position, Entry: $67,500, Current: $68,200, Size: 0.5 BTC
- ETH: No position

**Market Data (3-minute timeframe):**
BTC: Price $68,200, EMA20: $67,950, RSI7: 62, RSI14: 58, MACD: 120

**Instructions:**
Based on the data, decide whether to HOLD, BUY, or SELL. Provide reasoning.
"""

    # 生成决策
    decision = client.generate_decision(test_prompt)
    print("\n=== AI决策 ===")
    print(decision)

    # 如果需要，可以在运行时切换提供商
    # client.switch_provider('qwen_official')
    # decision2 = client.generate_decision(test_prompt)
