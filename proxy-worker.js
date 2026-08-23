/**
 * RP Hub 转发代理（Cloudflare Worker 版）
 *
 * 用途：浏览器直连某些第三方 API 时被拦（目标站 CORS / Origin 白名单，
 * 或 HTTPS 页面无法请求 HTTP 接口），用本 Worker 中转一次即可。
 *
 * 部署（约 2 分钟，免费额度够用）：
 *   1. https://dash.cloudflare.com 注册 → Workers 和 Pages → 创建 Worker
 *   2. 粘贴本文件全部代码 → 部署
 *   3. 得到形如 https://xxx.your-subdomain.workers.dev 的地址
 *   4. 在 RP Hub 设置 → 转发代理 里填：https://xxx.your-subdomain.workers.dev/?url=
 *      （注意末尾要带 ?url= ）
 *
 * 请求格式：{worker地址}?url={encodeURIComponent(目标完整URL)}
 * Worker 会以服务器身份请求目标，不携带浏览器 Origin/Referer，
 * 因此 sharellm 之类的 Origin 白名单不会触发。
 *
 * 安全说明：Key 会经过该 Worker（请只部署给自己用，别公开分享地址）。
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Max-Age': '86400'
};

export default {
  async fetch(request) {
    // 预检直接应答
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const target = url.searchParams.get('url');
    if (!target || !/^https?:\/\//i.test(target)) {
      return new Response('RP Hub Proxy: missing or invalid ?url= parameter', {
        status: 400,
        headers: CORS_HEADERS
      });
    }

    // 转发请求：去掉浏览器来源标识与 host 相关头
    const headers = new Headers(request.headers);
    ['origin', 'referer', 'host', 'cf-connecting-ip', 'cf-ipcountry',
      'cf-ray', 'x-forwarded-for', 'x-forwarded-proto', 'x-real-ip',
      'sec-fetch-site', 'sec-fetch-mode', 'sec-fetch-dest', 'sec-fetch-user'
    ].forEach(h => headers.delete(h));

    let upstream;
    try {
      upstream = await fetch(target, {
        method: request.method,
        headers,
        body: (request.method === 'GET' || request.method === 'HEAD') ? undefined : request.body,
        redirect: 'follow'
      });
    } catch (e) {
      return new Response('RP Hub Proxy upstream error: ' + e.message, {
        status: 502,
        headers: CORS_HEADERS
      });
    }

    // 透传响应，覆盖 CORS 头（保留流式，支持 SSE）
    const respHeaders = new Headers(upstream.headers);
    Object.entries(CORS_HEADERS).forEach(([k, v]) => respHeaders.set(k, v));
    respHeaders.delete('content-security-policy');

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: respHeaders
    });
  }
};
