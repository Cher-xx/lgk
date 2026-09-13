import React, { useEffect, useRef } from 'react';
import './ShapeGrid.css';

// A lighter background adaptation of the React Bits ShapeGrid component supplied by the user.
export default function ShapeGrid({ direction = 'diagonal', speed = .15, borderColor = 'rgba(191, 222, 193, .27)', squareSize = 68, hoverFillColor = 'rgba(174, 211, 174, .22)', hoverTrailAmount = 3, className = '' }) {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current, context = canvas.getContext('2d');
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const scale = Math.min(devicePixelRatio || 1, 2); let frame = null, visible = false, pageVisible = !document.hidden, x = 0, y = 0, hovered = null, trail = [];
    const resize = () => { const rect = canvas.getBoundingClientRect(); canvas.width = Math.round(rect.width * scale); canvas.height = Math.round(rect.height * scale); context.setTransform(scale, 0, 0, scale, 0, 0); };
    const draw = () => { const width = canvas.clientWidth, height = canvas.clientHeight, startX = -squareSize + x % squareSize, startY = -squareSize + y % squareSize; context.clearRect(0, 0, width, height); for (let left = startX; left < width + squareSize; left += squareSize) for (let top = startY; top < height + squareSize; top += squareSize) { const key = `${Math.floor((left - startX) / squareSize)},${Math.floor((top - startY) / squareSize)}`, index = trail.indexOf(key); if (key === hovered || (index !== -1 && index < hoverTrailAmount)) { context.globalAlpha = key === hovered ? 1 : Math.max(.18, 1 - index / (hoverTrailAmount + 1)); context.fillStyle = hoverFillColor; context.fillRect(left, top, squareSize, squareSize); context.globalAlpha = 1; } context.strokeStyle = borderColor; context.strokeRect(left + .5, top + .5, squareSize, squareSize); } };
    const loop = () => { if (!reduced) { const step = Math.max(speed, .05); if (direction === 'left' || direction === 'diagonal') x = (x - step + squareSize) % squareSize; if (direction === 'right') x = (x + step) % squareSize; if (direction === 'up' || direction === 'diagonal') y = (y - step + squareSize) % squareSize; if (direction === 'down') y = (y + step) % squareSize; } draw(); frame = !reduced && visible && pageVisible ? requestAnimationFrame(loop) : null; };
    const start = () => { if (!frame && visible && pageVisible) frame = requestAnimationFrame(loop); };
    const stop = () => { if (frame) cancelAnimationFrame(frame); frame = null; };
    const pointer = event => { const rect = canvas.getBoundingClientRect(), next = `${Math.floor((event.clientX - rect.left - x % squareSize) / squareSize)},${Math.floor((event.clientY - rect.top - y % squareSize) / squareSize)}`; if (next !== hovered) { if (hovered) trail = [hovered, ...trail].slice(0, hoverTrailAmount); hovered = next; if (reduced) draw(); } };
    const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; visible ? start() : stop(); }); const resizeObserver = new ResizeObserver(() => { resize(); draw(); }); const visibility = () => { pageVisible = !document.hidden; pageVisible ? start() : stop(); };
    resize(); draw(); observer.observe(canvas); resizeObserver.observe(canvas); canvas.addEventListener('pointermove', pointer); canvas.addEventListener('pointerleave', () => { hovered = null; if (reduced) draw(); }); document.addEventListener('visibilitychange', visibility);
    return () => { stop(); observer.disconnect(); resizeObserver.disconnect(); canvas.removeEventListener('pointermove', pointer); document.removeEventListener('visibilitychange', visibility); };
  }, [direction, speed, borderColor, squareSize, hoverFillColor, hoverTrailAmount]);
  return <canvas ref={canvasRef} className={`shapegrid-canvas ${className}`} aria-hidden="true"/>;
}
