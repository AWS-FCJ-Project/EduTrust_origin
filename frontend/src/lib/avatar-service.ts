import Cookies from 'js-cookie';

export interface AvatarUploadUrlResponse {
    upload_url: string;
    s3_key: string;
    avatar_url: string;
}

export async function getAvatarUploadUrl(): Promise<AvatarUploadUrlResponse | null> {
    try {
        const token = Cookies.get('auth_token');
        if (!token) return null;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        const response = await fetch(`${apiUrl}/user/avatar-upload-url`, {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) return null;
        return response.json();
    } catch {
        return null;
    }
}

export async function confirmAvatarUpload(s3Key: string): Promise<string | null> {
    try {
        const token = Cookies.get('auth_token');
        if (!token) return null;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        const response = await fetch(`${apiUrl}/user/avatar`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ s3_key: s3Key }),
        });

        if (!response.ok) return null;
        const data = await response.json();
        return data.avatar_url;
    } catch {
        return null;
    }
}

export async function uploadAvatar(file: File): Promise<string | null> {
    // Step 1: Get presigned upload URL
    const urls = await getAvatarUploadUrl();
    if (!urls) return null;

    // Step 2: Upload directly to S3 via presigned URL
    const uploadResponse = await fetch(urls.upload_url, {
        method: 'PUT',
        headers: {
            'Content-Type': file.type,
        },
        body: file,
    });

    if (!uploadResponse.ok) return null;

    // Step 3: Confirm upload and get permanent avatar URL
    const avatarUrl = await confirmAvatarUpload(urls.s3_key);
    return avatarUrl;
}