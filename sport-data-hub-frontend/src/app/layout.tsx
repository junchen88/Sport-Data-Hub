import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sport Data Hub",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <nav className="bg-blue-600 p-4 shadow-2xl/50 fixed top-0 w-screen h-auto z-50">
          <div className="flex items-center">
            <div className="w-3/8">
              <h2 className="text-xl font-bold">Sport Data Hub</h2>
            </div>
            <ul className="flex w-5/8 gap-x-[10vw]">
              <li><h3>Football</h3></li>
              <li><h3>b</h3></li>
              <li><h3>c</h3></li>
              <li><h3>d</h3></li>
              <li><h3>e</h3></li>
            </ul>
          </div>
        </nav>
        
        
        
        {children}
      </body>
    </html>
  );
}
