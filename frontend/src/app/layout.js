import './globals.css';

export const metadata = {
  title: 'Indian Law RAG | Legal Assistant',
  description: 'AI-powered legal assistant for Indian Law, backed by a retrieval-augmented generation engine.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        <div className="app-layout">
          {children}
        </div>
      </body>
    </html>
  );
}
