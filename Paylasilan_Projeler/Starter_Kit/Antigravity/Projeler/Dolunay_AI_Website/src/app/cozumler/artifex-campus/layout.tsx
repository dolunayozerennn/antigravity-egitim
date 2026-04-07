import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Artifex Campus',
  description: 'İşletmenizi AI ile dönüştürecek hazır çözüm paketleri. Personel tasarrufu sağlayan otonom B2B yapay zeka otomasyonları.',
  openGraph: {
    title: 'Artifex Campus | dolunay.ai',
    description: 'İşletmenizi AI ile dönüştürecek hazır çözüm paketleri. Personel tasarrufu sağlayan otonom B2B yapay zeka otomasyonları.',
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
