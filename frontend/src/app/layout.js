import './globals.css';

export const metadata = {
  title: 'Nyaya AI — Indian Law Assistant',
  description: 'AI-powered legal assistant for Indian Law. Ask questions about the Indian Constitution, BNS, BNSS, IT Act and more.',
  keywords: 'Indian law, legal assistant, Constitution of India, BNS, BNSS, IT Act, AI legal advisor',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#06090f" />
      </head>
      <body>
        <div className="app-layout">
          {children}
        </div>
      </body>
    </html>
  );
}
