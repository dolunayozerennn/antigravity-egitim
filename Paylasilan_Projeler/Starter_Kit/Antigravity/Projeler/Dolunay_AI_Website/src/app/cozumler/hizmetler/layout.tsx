import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hizmetler',
  description: 'Dolunay.ai işletmelere yönelik profesyonel yapay zeka çözümleri ve hizmetleri.',
  openGraph: {
    title: 'Hizmetler | dolunay.ai',
    description: 'Dolunay.ai işletmelere yönelik profesyonel yapay zeka çözümleri ve hizmetleri.',
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
