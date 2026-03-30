import ExamPageClient from './ExamPageClient';

export function generateStaticParams() {
  return [{ id: 'null' }];
}

export default function Page() {
  return <ExamPageClient />;
}
