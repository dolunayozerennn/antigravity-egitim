import type { Metadata } from 'next'
import { DM_Sans, Space_Grotesk } from 'next/font/google'
import { LanguageProvider } from '@/i18n/i18n'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import './globals.css'

const dmSans = DM_Sans({
  subsets: ['latin', 'latin-ext'],
  variable: '--font-dm-sans',
  display: 'swap',
})

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin', 'latin-ext'],
  variable: '--font-space-grotesk',
  display: 'swap',
})

export const metadata: Metadata = {
  metadataBase: new URL('https://dolunay.ai'),
  title: {
    default: 'dolunay.ai — Yapay Zeka Eğitmen & Builder',
    template: '%s | dolunay.ai',
  },
  description: 'Yapay zeka eğitmeni & builder. İşletmeler için AI otomasyon çözümleri, girişimciler için AI Factory topluluğu.',
  keywords: ['yapay zeka', 'AI eğitim', 'otomasyon', 'dolunay özeren', 'AI Factory', 'kurumsal eğitim', 'artificial intelligence', 'yapay zeka danışmanlık'],
  authors: [{ name: 'Dolunay Özeren' }],
  creator: 'dolunay.ai',
  openGraph: {
    type: 'website',
    locale: 'tr_TR',
    url: 'https://dolunay.ai',
    siteName: 'dolunay.ai',
    title: 'dolunay.ai — Yapay Zeka Eğitmen & Builder',
    description: 'Yapay zeka eğitmeni & builder. İşletmeler için AI otomasyon çözümleri, girişimciler için AI Factory topluluğu.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'dolunay.ai — Yapay Zeka Eğitmen & Builder',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'dolunay.ai — Yapay Zeka Eğitmen & Builder',
    description: 'Yapay zeka eğitmeni & builder. İşletmeler için AI otomasyon çözümleri.',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  alternates: {
    canonical: 'https://dolunay.ai',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="tr" className={`${dmSans.variable} ${spaceGrotesk.variable}`} suppressHydrationWarning>
      <head>
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      </head>
      <body className="min-h-screen bg-gray-950 text-white font-sans selection:bg-purple-500/30">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'Organization',
              name: 'dolunay.ai',
              url: 'https://dolunay.ai',
              logo: 'https://dolunay.ai/favicon.svg',
              founder: {
                '@type': 'Person',
                name: 'Dolunay Özeren',
                jobTitle: 'AI Eğitmen & Builder',
              },
              sameAs: [
                'https://www.instagram.com/dolunay_ozeren/',
                'https://youtube.com/@dolunayozeren',
                'https://tiktok.com/@dolunayozeren',
              ],
              description: 'Yapay zeka eğitmeni & builder. İşletmeler için AI otomasyon çözümleri, girişimciler için AI Factory topluluğu.',
            }),
          }}
        />
        <LanguageProvider>
          <Navbar />
          <main className="pt-20">
            {children}
          </main>
          <Footer />
        </LanguageProvider>
      </body>
    </html>
  )
}
