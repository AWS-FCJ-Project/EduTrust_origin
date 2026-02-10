export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        // Get EC2 host from environment variable
        const ec2Host = env.EC2_HOST || '54.169.189.61';
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
            // Create a new Request object to avoid "body already used" and header issues
            const proxyRequest = new Request(backendUrl, {
                method: request.method,
                headers: new Headers(request.headers),
                // Only pass body for non-GET/HEAD methods
                body: (request.method !== 'GET' && request.method !== 'HEAD') ? request.body : null,
                redirect: 'follow'
            });

            // CRITICAL: Remove Host header so Cloudflare fetch() sets it automatically for EC2
            proxyRequest.headers.delete('Host');

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
