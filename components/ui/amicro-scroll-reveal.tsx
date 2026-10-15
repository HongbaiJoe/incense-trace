'use client';
// Amicro, Syed Subhan Uddin. MIT; see licenses/AMICRO.txt.
import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface ScrollRevealProps {
  children: React.ReactNode;
  duration?: number;
  yOffset?: number;
  xOffset?: number;
  scale?: number;
  className?: string;
}

export function ScrollReveal({
  children,
  duration = 0.6,
  yOffset = 30,
  xOffset = 0,
  scale = 0.95,
  className = '',
}: ScrollRevealProps) {
  const reduced=useReducedMotion();
  return (
    <motion.div
      initial={reduced?false:{ opacity: 0, y: yOffset, x: xOffset, scale }}
      whileInView={{ opacity: 1, y: 0, x: 0, scale: 1 }}
      viewport={{ once: true, margin: '-15%' }}
      transition={{
        duration,
        ease: [0.16, 1, 0.3, 1], // easeOutExpo
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

