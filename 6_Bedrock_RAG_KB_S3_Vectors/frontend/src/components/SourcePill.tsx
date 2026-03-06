interface SourcePillProps {
  uri: string;
}

export default function SourcePill({ uri }: SourcePillProps) {
  const filename = uri.split('/').pop()?.replace(/_/g, ' ').replace(/\.md$/, '') ?? uri;
  return (
    <span className="inline-block bg-[#2a2000] text-aws-orange border border-aws-orange rounded px-2.5 py-0.5 text-xs font-mono mr-1.5 mb-1.5">
      {filename}
    </span>
  );
}
