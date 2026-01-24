/**
 * Renders messages: user (right, dark bg) and assistant (left, border, ReactMarkdown).
 * renderContent: string -> Markdown for assistant, pre-wrap for user; ContentBlock[]
 * -> text (Markdown or pre-wrap by role) and image (data URL from base64). markdownComponents
 * styles h1–h3, p, ul, ol, li, strong, em, code (inline vs block), blockquote, hr.
 */
import { AlertCircle, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage } from '../types';

interface MessageListProps {
  messages: ChatMessage[];
}

/** ReactMarkdown components for assistant messages: headings, lists, bold, code, blockquote, hr. */
const markdownComponents = {
  h1: ({ node, ...props }: any) => <h1 className="text-xl font-bold text-gray-900 mt-4 mb-2 first:mt-0" {...props} />,
  h2: ({ node, ...props }: any) => <h2 className="text-lg font-semibold text-gray-900 mt-3 mb-2 first:mt-0" {...props} />,
  h3: ({ node, ...props }: any) => <h3 className="text-base font-semibold text-gray-800 mt-2 mb-1 first:mt-0" {...props} />,
  p: ({ node, ...props }: any) => <p className="text-gray-700 mb-3 leading-relaxed" {...props} />,
  ul: ({ node, ...props }: any) => <ul className="list-disc list-inside mb-3 space-y-1 text-gray-700" {...props} />,
  ol: ({ node, ...props }: any) => <ol className="list-decimal list-inside mb-3 space-y-1 text-gray-700" {...props} />,
  li: ({ node, ...props }: any) => <li className="ml-4" {...props} />,
  strong: ({ node, ...props }: any) => <strong className="font-semibold text-gray-900" {...props} />,
  em: ({ node, ...props }: any) => <em className="italic text-gray-700" {...props} />,
  code: ({ node, inline, ...props }: any) =>
    inline ? <code className="bg-gray-200 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props} /> : <code className="block bg-gray-200 p-3 rounded text-sm font-mono text-gray-800 overflow-x-auto mb-3" {...props} />,
  blockquote: ({ node, ...props }: any) => <blockquote className="border-l-4 border-primary-500 pl-4 italic text-gray-600 my-3" {...props} />,
  hr: ({ node, ...props }: any) => <hr className="my-4 border-gray-300" {...props} />,
};

export default function MessageList({ messages }: MessageListProps) {
  const renderContent = (content: ChatMessage['content'], role: 'user' | 'assistant') => {
    if (typeof content === 'string') {
      if (role === 'assistant') {
        return (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown components={markdownComponents}>
              {content}
            </ReactMarkdown>
          </div>
        );
      }
      // For user messages, keep simple text formatting
      return <p className="whitespace-pre-wrap">{content}</p>;
    }

    return (
      <div className="space-y-2">
        {content.map((block, index) => (
          <div key={index}>
            {block.text && (
              <div className="mb-2">
                {role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown components={markdownComponents}>
                      {block.text}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{block.text}</p>
                )}
              </div>
            )}
            {block.image && (
              <div className="mt-2">
                <img
                  src={`data:image/${block.image.format};base64,${block.image.source.bytes}`}
                  alt="Uploaded"
                  className="max-w-full max-h-64 rounded-lg border border-gray-200"
                />
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {messages.map((message, index) => (
        <div
          key={index}
          className={`flex gap-4 ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          {message.role === 'assistant' && (
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-primary-600" />
            </div>
          )}

          <div
            className={`max-w-[80%] md:max-w-[70%] rounded-lg px-4 py-3 ${
              message.role === 'user'
                ? 'bg-primary-600 text-white'
                : 'bg-white border border-gray-200 shadow-sm'
            }`}
          >
            {renderContent(message.content, message.role)}
          </div>

          {message.role === 'user' && (
            <div className="flex-shrink-0 w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-gray-600" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
