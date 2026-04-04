import time
import httpx

from config.models import AppConfig, MemberConfig


class MemberService:
    def list_members(self, config: AppConfig, type_filter: str | None = None) -> list[MemberConfig]:
        members = config.members
        if type_filter:
            members = [m for m in members if m.type == type_filter]
        return members

    async def ping(self, member: MemberConfig) -> dict:
        if member.type != "service":
            return {"status": "error", "error": "ping only supports type=service"}
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{member.serviceUrl}/api/v1/service/info")
            latency = int((time.monotonic() - start) * 1000)
            if resp.status_code == 200:
                return {"status": "connected", "latency_ms": latency, "service_info": resp.json()}
            else:
                return {"status": "disconnected", "error": f"{resp.status_code}"}
        except Exception as e:
            return {"status": "disconnected", "error": str(e), "message": f"无法连接到 {member.serviceUrl}"}
