"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

export default function SimpleTest() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleClick = () => {
    setLoading(true);
    setTimeout(() => {
      setCount(count + 1);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        
        <h1 className="text-3xl font-bold text-gray-900">Component Test</h1>

        
        <Card>
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Button</h2>
          <div className="flex gap-2 mb-4">
            <Button onClick={handleClick} isLoading={loading}>
              Click me ({count})
            </Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="danger">Danger</Button>
          </div>
          <div className="flex gap-2">
            <Button size="sm">Small</Button>
            <Button size="md">Medium</Button>
            <Button size="lg">Large</Button>
          </div>
        </Card>

        
        <Card>
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Input</h2>
          <Input 
            label="Name"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          {name && <p className="mt-2 text-sm text-gray-900">Hello, young padawan {name}!</p>}
        </Card>

        
        <Card>
          <h2 className="text-xl font-semibold mb-2 text-gray-900">Card</h2>
          <p className="text-gray-600">CARD</p>
        </Card>

        <Card hover>
          <h2 className="text-xl font-semibold mb-2 text-gray-900">Hover Card</h2>
          <p className="text-gray-600">I AM SHADOW!</p>
        </Card>

        <Card hover onClick={() => alert('YOU DARE TO CLICK ME?')}>
          <h2 className="text-xl font-semibold mb-2 text-gray-900">Clickable Card</h2>
          <p className="text-gray-600">CLICK ME!</p>
        </Card>

      </div>
    </div>
  );
}