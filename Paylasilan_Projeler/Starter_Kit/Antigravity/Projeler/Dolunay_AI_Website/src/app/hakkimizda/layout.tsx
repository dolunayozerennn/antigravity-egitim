import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hakkımızda',
  description: 'Dolunay.ai ekibi ile tanışın. İnsan ve yapay zeka entegrasyonuyla çalışan hibrid takımımız ve vizyonumuz.',
  openGraph: {
    title: 'Hakkımızda | dolunay.ai',
    description: 'Dolunay.ai ekibi ile tanışın. İnsan ve yapay zeka entegrasyonuyla çalışan hibrid takımımız ve vizyonumuz.',
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
