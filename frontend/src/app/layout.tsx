import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Edutrust",
  description: "EduTrust frontend",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css"
          integrity="sha384-G79zsp0QlqdadpBn6AiHGL6TSc0tT84no0VAn4Kv05uKNI69Yp5fKdzfOTFBMGth"
          crossOrigin="anonymous"
        />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
