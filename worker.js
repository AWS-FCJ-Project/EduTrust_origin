export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        // Get EC2 host from environment variable
        const ec2Host = env.EC2_HOST || 'YOUR_EC2_PUBLIC_IP';
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
            // Create a new set of headers, removing the Host header to avoid Error 1003
            const newHeaders = new Headers(request.headers);
            newHeaders.delete('host');

            const response = await fetch(backendUrl, {
                method: request.method,
                headers: newHeaders,
                body: request.body,
                redirect: 'follow'
            });

            // Clone response and add CORS headers
            const newResponse = new Response(response.body, response);
            newResponse.headers.set('Access-Control-Allow-Origin', '*');

            return newResponse;
        } catch (error) {
            return new Response(JSON.stringify({ error: 'Backend unavailable' }), {
                status: 503,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
            });
        }
    },
};
