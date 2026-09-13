// Adapted from the React Bits ClickSpark source supplied with this project.
// A viewport canvas avoids allocating a canvas as tall as the entire gallery.
import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import ShapeGrid from './ShapeGrid';

function HeroShapeGrid() {
  const [hero, setHero] = useState(null);
  useEffect(() => setHero(document.querySelector('.hero')), []);
  return hero ? createPortal(<ShapeGrid className="hero-shape-grid" direction="diagonal" speed={.15} squareSize={68} borderColor="rgba(191, 222, 193, .27)" hoverFillColor="rgba(174, 211, 174, .22)" hoverTrailAmount={3}/>, hero) : null;
}

export default function ClickSpark({ sparkColor = '#8ec9a2', sparkSize = 10, sparkRadius = 24, sparkCount = 8, duration = 450, extraScale = 1, children }) {
  const canvasRef = useRef(null);
  const sparks = useRef([]);
  const [host, setHost] = useState(document.body);
  useEffect(() => {
    let frame;
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    function draw(now) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const dpr = Math.min(devicePixelRatio || 1, 2);
      if (canvas.width !== Math.round(innerWidth * dpr) || canvas.height !== Math.round(innerHeight * dpr)) {
        canvas.width = Math.round(innerWidth * dpr); canvas.height = Math.round(innerHeight * dpr);
      }
      const ctx = canvas.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      sparks.current = sparks.current.filter(s => now - s.startTime < duration);
      for (const s of sparks.current) {
        const t = Math.max(0, (now - s.startTime) / duration), eased = t * (2 - t);
        const distance = eased * sparkRadius * extraScale, length = sparkSize * (1 - eased);
        ctx.strokeStyle = sparkColor; ctx.lineWidth = 2; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(s.x + distance * Math.cos(s.angle), s.y + distance * Math.sin(s.angle));
        ctx.lineTo(s.x + (distance + length) * Math.cos(s.angle), s.y + (distance + length) * Math.sin(s.angle)); ctx.stroke();
      }
      frame = sparks.current.length ? requestAnimationFrame(draw) : null;
    }
    function click(e) {
      if (motion.matches || e.detail === 0) return;
      setHost(e.target.closest('dialog[open]') || document.body);
      const startTime = performance.now();
      sparks.current.push(...Array.from({length:sparkCount}, (_, i) => ({x:e.clientX,y:e.clientY,angle:2*Math.PI*i/sparkCount,startTime})));
      cancelAnimationFrame(frame); frame = requestAnimationFrame(draw);
    }
    document.addEventListener('click', click, true);
    return () => {document.removeEventListener('click', click, true);cancelAnimationFrame(frame);};
  }, [sparkColor, sparkSize, sparkRadius, sparkCount, duration, extraScale]);
  return <>{children}<HeroShapeGrid />{createPortal(<canvas ref={canvasRef} className="click-spark-canvas" aria-hidden="true"/>, host)}</>;
}
