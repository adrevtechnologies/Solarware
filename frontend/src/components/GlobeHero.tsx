import React, { useEffect, useRef } from 'react';

export const GlobeHero: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let rotation = 0;

    const animate = () => {
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = 80;

      // Clear canvas with white background
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, width, height);

      // Draw subtle glow
      const gradient = ctx.createRadialGradient(
        centerX,
        centerY,
        radius * 0.6,
        centerX,
        centerY,
        radius * 1.3
      );
      gradient.addColorStop(0, 'rgba(34, 197, 94, 0.2)');
      gradient.addColorStop(1, 'rgba(34, 197, 94, 0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);

      // Draw globe
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate((rotation * Math.PI) / 180);

      // Ocean (blue circle)
      ctx.fillStyle = '#1e40af';
      ctx.beginPath();
      ctx.arc(0, 0, radius, 0, Math.PI * 2);
      ctx.fill();

      // Continents (green shapes)
      ctx.fillStyle = '#22c55e';

      // Africa
      ctx.fillRect(-20, -30, 40, 60);

      // Europe
      ctx.fillRect(20, -40, 30, 30);

      // Americas
      ctx.fillRect(-70, -40, 25, 80);

      // Globe border
      ctx.strokeStyle = '#0369a1';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(0, 0, radius, 0, Math.PI * 2);
      ctx.stroke();

      // Grid lines
      ctx.strokeStyle = 'rgba(3, 105, 161, 0.2)';
      ctx.lineWidth = 1;

      // Horizontal lines
      for (let i = -60; i <= 60; i += 30) {
        ctx.beginPath();
        ctx.moveTo(-radius, i);
        ctx.lineTo(radius, i);
        ctx.stroke();
      }

      // Vertical lines
      for (let i = -radius; i <= radius; i += 40) {
        ctx.beginPath();
        ctx.moveTo(i, -radius);
        ctx.lineTo(i, radius);
        ctx.stroke();
      }

      ctx.restore();

      // Slow rotation
      rotation += 0.2;

      requestAnimationFrame(animate);
    };

    animate();
  }, []);

  return (
    <div className="w-full bg-gradient-to-b from-gray-50 to-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex flex-col items-center justify-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-2">Solarware</h1>
          <p className="text-lg text-gray-600 mb-8">Commercial Solar Prospect Discovery</p>
          <canvas ref={canvasRef} width={300} height={300} className="drop-shadow-lg" />
        </div>
      </div>
    </div>
  );
};
