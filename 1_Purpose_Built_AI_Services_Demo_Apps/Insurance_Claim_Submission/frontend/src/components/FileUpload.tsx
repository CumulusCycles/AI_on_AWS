import { useRef, useState, useCallback } from 'react';

interface FileUploadProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
  error?: string;
}

export default function FileUpload({ files, onFilesChange, disabled, error }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = droppedFiles.filter(file => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      return ['.pdf', '.png'].includes(ext);
    });

    onFilesChange([...files, ...validFiles]);
  }, [files, onFilesChange, disabled]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      onFilesChange([...files, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  const getFileThumbnail = (file: File): string | null => {
    if (file.type.startsWith('image/')) {
      return URL.createObjectURL(file);
    }
    return null;
  };

  return (
    <div className="space-y-2">
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : disabled
            ? 'border-gray-300 bg-gray-50'
            : 'border-gray-400 hover:border-gray-500 cursor-pointer'
        }`}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.png"
          onChange={handleFileInputChange}
          disabled={disabled}
          className="hidden"
        />
        <p className="text-gray-600">
          {isDragging ? 'Drop files here' : 'Drag and drop files here, or click to select'}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          PDF or PNG files (max 10MB each)
        </p>
      </div>

      {error && (
        <p className="text-red-600 text-sm">{error}</p>
      )}

      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold">Selected Files ({files.length}):</p>
          <div className="grid grid-cols-2 gap-2">
            {files.map((file, index) => {
              const thumbnail = getFileThumbnail(file);
              return (
                <div
                  key={index}
                  className="border border-gray-300 rounded p-2 flex items-center space-x-2"
                >
                  {thumbnail ? (
                    <img
                      src={thumbnail}
                      alt={file.name}
                      className="w-12 h-12 object-cover rounded"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                      <span className="text-xs">PDF</span>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  {!disabled && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(index);
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      ×
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

