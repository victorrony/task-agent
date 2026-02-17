'use client';

import { useState, useEffect } from 'react';
import { fetchUsers, UserProfile } from '@/lib/api';
import { ChevronDown } from 'lucide-react';

interface UserSelectorProps {
  currentUserId: number;
  onUserChange: (userId: number) => void;
}

export default function UserSelector({ currentUserId, onUserChange }: UserSelectorProps) {
  const [users, setUsers] = useState<UserProfile[]>([]);

  useEffect(() => {
    fetchUsers().then(setUsers).catch(() => {
      setUsers([{ id: 1, name: 'Utilizador Principal' }]);
    });
  }, []);

  if (users.length <= 1) return null;

  return (
    <div className="relative flex items-center gap-2 bg-slate-800/50 pl-4 pr-2 py-2 rounded-lg border border-slate-700">
      <select
        value={currentUserId}
        onChange={(e) => onUserChange(Number(e.target.value))}
        className="bg-transparent text-sm text-white appearance-none pr-6 focus:outline-none cursor-pointer"
      >
        {users.map(u => (
          <option key={u.id} value={u.id} className="bg-slate-800">{u.name}</option>
        ))}
      </select>
      <ChevronDown size={14} className="absolute right-3 text-slate-400 pointer-events-none" />
    </div>
  );
}
