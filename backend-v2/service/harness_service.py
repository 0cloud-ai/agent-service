from config.models import AppConfig


class HarnessService:
    def get_compatible_providers(self, harness_id: str, config: AppConfig) -> list[str]:
        engine = config.harnesses.engines.get(harness_id)
        if engine is None:
            return []
        compatible = []
        for name, provider in config.providers.items():
            if provider.apiFormat in engine.apiFormats:
                compatible.append(name)
        return compatible

    def validate_binding(self, harness_id: str, provider_name: str, config: AppConfig) -> bool:
        engine = config.harnesses.engines.get(harness_id)
        provider = config.providers.get(provider_name)
        if engine is None or provider is None:
            return False
        return provider.apiFormat in engine.apiFormats
