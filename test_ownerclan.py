import httpx
import asyncio

async def test():
    try:
        resp = await httpx.AsyncClient().post('https://auth.ownerclan.com/auth', json={'username':'a', 'password':'b'}, timeout=3)
        print("Auth URL exists:", resp.status_code)
    except Exception as e:
        print("Auth Exception:", e)

    try:
        resp = await httpx.AsyncClient().get('https://api.ownerclan.com/v1/products/new', timeout=3)
        print("API URL exists:", resp.status_code)
    except Exception as e:
        print("API Exception:", e)

asyncio.run(test())
