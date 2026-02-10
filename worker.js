export default {
    async fetch(request, env) {
        const url = new URL(request.url);
        const ec2Host = env.EC2_HOST || 'ec2-54-169-189-61.ap-southeast-1.compute.amazonaws.com';
        const backendUrl = `http://${ec2Host}:8000${url.pathname}${url.search}`;

        // Handle CORS preflight
        if (request.method === 'OPTIONS') {
            return new Response(null, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
            });
        }

        try {
            const blockedHeaders = new Set([
                'host',
                'cf-connecting-ip',
                'cf-ipcountry',
                'cf-ray',
                'cf-visitor',
                'x-forwarded-host',
                'x-forwarded-proto',
                'x-real-ip',
            ]);
            const proxyHeaders = new Headers();
            for (const [key, value] of request.headers.entries()) {
                if (!blockedHeaders.has(key.toLowerCase())) {
                    proxyHeaders.set(key, value);
                }
            }

            const proxyRequest = new Request(backendUrl, {
                method: request.method,
                headers: proxyHeaders,
                body: (request.method !== 'GET' && request.method !== 'HEAD') ? request.body : null,
                // Prevent redirect loops to workers.dev from origin responses.
                redirect: 'manual'
            });

            const response = await fetch(proxyRequest);

            // Clone response and add CORS headers
            const newResponse = new Response(response.body, response);
            newResponse.headers.set('Access-Control-Allow-Origin', '*');

            return newResponse;
        } catch (error) {
            return new Response(JSON.stringify({
                error: 'Proxy Error',
                message: error.message,
                target: backendUrl
            }), {
                status: 502,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
            });
        }
    },
};
