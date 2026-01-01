import { useRef, useEffect, useState } from 'react';

interface BoundingBox {
  width: number;
  height: number;
  left: number;
  top: number;
}

interface LabelInstance {
  bounding_box: BoundingBox;
  confidence: number;
}

interface Label {
  name: string;
  confidence: number;
  translated_name?: string;
  instances?: LabelInstance[];
}

interface ImageWithLabelsProps {
  imageFile: File | null;
  labels: Label[];
}

export default function ImageWithLabels({ imageFile, labels }: ImageWithLabelsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);

  // Create object URL from file
  useEffect(() => {
    if (imageFile) {
      const url = URL.createObjectURL(imageFile);
      setImageUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [imageFile]);

  // Load image and draw labels
  useEffect(() => {
    if (!imageUrl || !canvasRef.current || labels.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = () => {
      // Set canvas size to match image
      canvas.width = img.width;
      canvas.height = img.height;
      setImageSize({ width: img.width, height: img.height });
      imageRef.current = img;

      // Draw image
      ctx.drawImage(img, 0, 0);

      // Draw bounding boxes and labels
      const colors = [
        '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF',
        '#00FFFF', '#FFA500', '#800080', '#FFC0CB', '#A52A2A'
      ];

      labels.forEach((label, labelIndex) => {
        if (!label.instances || label.instances.length === 0) return;

        const color = colors[labelIndex % colors.length];
        const labelText = label.translated_name || label.name;
        
        label.instances.forEach((instance) => {
          if (!instance.bounding_box) return;
          
          const bbox = instance.bounding_box;
          
          // Convert normalized coordinates to pixel coordinates
          const x = bbox.left * img.width;
          const y = bbox.top * img.height;
          const width = bbox.width * img.width;
          const height = bbox.height * img.height;

          // Draw bounding box
          ctx.strokeStyle = color;
          ctx.lineWidth = 3;
          ctx.strokeRect(x, y, width, height);

          // Draw label background
          const confidenceText = `${(instance.confidence || label.confidence).toFixed(0)}%`;
          const fullText = `${labelText} (${confidenceText})`;
          
          ctx.font = 'bold 14px Arial';
          const textMetrics = ctx.measureText(fullText);
          const textWidth = textMetrics.width;
          const textHeight = 20;
          
          // Draw background rectangle for text
          ctx.fillStyle = color;
          ctx.globalAlpha = 0.7;
          ctx.fillRect(x, y - textHeight - 4, textWidth + 8, textHeight);
          ctx.globalAlpha = 1.0;

          // Draw label text
          ctx.fillStyle = '#FFFFFF';
          ctx.fillText(fullText, x + 4, y - 6);
        });
      });
    };

    img.src = imageUrl;
  }, [imageUrl, labels]);

  if (!imageFile || !imageUrl) {
    return null;
  }

  return (
    <div className="relative inline-block">
      <canvas
        ref={canvasRef}
        className="max-w-full h-auto border border-gray-300 rounded-lg"
        style={{ display: 'block' }}
      />
      {imageSize && (
        <div className="mt-2 text-xs text-gray-500">
          Image: {imageSize.width} × {imageSize.height}px
        </div>
      )}
    </div>
  );
}

