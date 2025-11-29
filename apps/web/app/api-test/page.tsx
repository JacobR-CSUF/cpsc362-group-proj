"use client";

import React, { useState } from 'react';
import { api } from '@/lib/api';

export default function APITestPage() {
  const [status, setStatus] = useState('Not tested');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const testAPI = async () => {
    setLoading(true);
    setStatus('Testing...');
    setResult(null);
    
    try {
      const res = await api.get('/');
      setStatus('✅ SUCCESS - API Connected!');
      setResult(res.data);
    } catch (error: any) {
      setStatus('❌ FAILED - Cannot connect');
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">API Test</h1>
          
          <div className="mb-4">
            <p className="text-lg text-gray-900">{status}</p>
          </div>
          
          <button
            onClick={testAPI}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Testing...' : 'Test API Connection'}
          </button>
        </div>

        {result && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Response</h2>
            <pre className="bg-gray-900 text-green-400 p-4 rounded overflow-x-auto text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}