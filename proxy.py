#!python
from datetime import datetime
import logging
import sys
from urllib.parse import urljoin

import asyncio
import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)


TARGET_SERVER_PROTOCOL = 'http'
TARGET_SERVER_HOST = 'example.com'

START_TIME = None
BYTES_TOTAL = 0

async def proxy(request):

    target_url = TARGET_SERVER_PROTOCOL + '://' + TARGET_SERVER_HOST
    target_url = urljoin(target_url, request.match_info['path'])

    headers = dict(request.headers)

    # Get range from query params or headers
    range = request.query.get('range', '')
    if range:
        range_headers = request.headers.get('Range', range)
        if range != range_headers:
            raise web.HTTPRequestRangeNotSatisfiable()
        #@TODO: pass range from query params to headers

    data = await request.read()
    get_data = request.rel_url.query

    async with aiohttp.ClientSession() as session:
        headers['Host'] = TARGET_SERVER_HOST
        async with session.request(request.method, target_url, headers=headers, params=get_data, data=data) as resp:
            res = resp
            raw = await res.read()

    content_type = res.headers.get('Content-Type')

    # Yes, globals are bad, but let's use here
    global BYTES_TOTAL
    BYTES_TOTAL += len(raw)
    return web.Response(body=raw, headers={'Content-Type': content_type})


async def stats(request):
    uptime = datetime.now() - START_TIME
    return web.Response(text=f'Bytes {BYTES_TOTAL} uptime {uptime.seconds}')

if __name__ == "__main__":

    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(logging.StreamHandler(sys.stdout))

    app = web.Application()
    app.router.add_route('get', '/stats', stats)
    app.router.add_route('*', '/{path:.*?}', proxy)

    loop = asyncio.get_event_loop()
    f = loop.create_server(app.make_handler(), '0.0.0.0', 8880)
    srv = loop.run_until_complete(f)
    print('serving on', srv.sockets[0].getsockname())
    try:
        START_TIME = datetime.now()
        loop.run_forever()
    except KeyboardInterrupt:
        pass