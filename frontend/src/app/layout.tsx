import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@propelauth/nextjs/client";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Pure — Swing Pure",
  description:
    "Compare your golf swing to Tiger Woods' iconic 2000 form. Get your top 3 faults and drills to improve.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <AuthProvider authUrl={process.env.NEXT_PUBLIC_AUTH_URL!}>
          <Header />
          <main className="pt-16">{children}</main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
