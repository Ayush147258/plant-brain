'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border h-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="text-xl font-bold font-sans tracking-tight">
            <span className="text-text-primary">Plant</span>
            <span className="text-accent-cyan">Brain</span>
          </div>
        </Link>

        <div className="hidden md:flex items-center space-x-8">
          <Link href="/#how" className="text-sm font-medium text-text-secondary hover:text-text-primary transition-colors">How It Works</Link>
          <Link href="/#outcomes" className="text-sm font-medium text-text-secondary hover:text-text-primary transition-colors">Outcomes</Link>
          <Link href="/#who" className="text-sm font-medium text-text-secondary hover:text-text-primary transition-colors">Who It's For</Link>
          <Link href="/#cta" className="px-4 py-2 text-sm font-semibold rounded-md border border-accent-cyan text-accent-cyan hover:bg-accent-cyan/10 transition-colors">Request Demo</Link>
        </div>

        <div className="md:hidden flex items-center">
          <button onClick={() => setIsOpen(!isOpen)} className="text-text-primary focus:outline-none p-2" aria-label="Toggle navigation">
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="md:hidden absolute top-16 left-0 right-0 bg-surface border-b border-border shadow-lg">
          <div className="flex flex-col px-4 pt-2 pb-6 space-y-4">
            <Link href="/#how" onClick={() => setIsOpen(false)} className="text-text-secondary hover:text-text-primary block px-2 py-1">How It Works</Link>
            <Link href="/#outcomes" onClick={() => setIsOpen(false)} className="text-text-secondary hover:text-text-primary block px-2 py-1">Outcomes</Link>
            <Link href="/#who" onClick={() => setIsOpen(false)} className="text-text-secondary hover:text-text-primary block px-2 py-1">Who It's For</Link>
            <Link href="/#cta" onClick={() => setIsOpen(false)} className="w-full text-center px-4 py-2 mt-2 text-sm font-semibold rounded-md border border-accent-cyan text-accent-cyan hover:bg-accent-cyan/10 transition-colors">Request Demo</Link>
          </div>
        </div>
      )}
    </nav>
  );
}