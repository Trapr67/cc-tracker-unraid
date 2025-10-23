import React, {useEffect, useState} from 'react';
import Login from './components/Login';
import CardList from './components/CardList';
import Dashboard from './components/Dashboard';
import CalendarView from './components/CalendarView';
import Settings from './components/Settings';
import AdminUsers from './components/AdminUsers';
import { whoami, getStatuses, logout } from './api';

export default function App(){
  const [user, setUser] = useState(null);
  const [statuses, setStatuses] = useState([]);
  const [tab, setTab] = useState('cards');
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(()=>{ 
    (async()=>{ 
      try{ 
        const r = await whoami(); 
        if(r.user) setUser(r.user);
      }catch(e){} 
    })(); 
  }, []);

  useEffect(()=>{ 
    if(user) refresh(); 
  }, [user]);

  async function refresh(){
    const s = await getStatuses();
    setStatuses(s);
  }

  if(!user) return (
    <Login onLogin={async()=>{
      const r = await whoami(); 
      if(r.user) setUser(r.user);
    }}/>
  );

  return (
    <div className="container">
      <header style={{
        display:'flex',
        justifyContent:'space-between',
        alignItems:'center',
        marginBottom:8
      }}>
        <h1>Credit Card Tracker</h1>

        {/* Hamburger Menu */}
        <div className="hamburger-menu">
          <button 
            className="menu-btn" 
            onClick={()=>setMenuOpen(!menuOpen)}
            aria-label="Menu"
          >
            ☰
          </button>

          {menuOpen && (
            <div className="menu-dropdown">
              <a onClick={()=>{setTab('cards');setMenuOpen(false)}}>Cards</a>
              <a onClick={()=>{setTab('dashboard');setMenuOpen(false)}}>Dashboard</a>
              <a onClick={()=>{setTab('calendar');setMenuOpen(false)}}>Calendar</a>
              {user.is_admin && <>
                <a onClick={()=>{setTab('users');setMenuOpen(false)}}>Users</a>
                <a onClick={()=>{setTab('settings');setMenuOpen(false)}}>Settings</a>
              </>}
              <a onClick={async()=>{
                await logout(); 
                setUser(null);
                setMenuOpen(false);
              }}>Logout</a>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      {tab==='dashboard' && <Dashboard statuses={statuses}/>}
      {tab==='calendar' && <CalendarView statuses={statuses}/>}
      {tab==='cards' && <CardList statuses={statuses} refresh={refresh}/>}
      {tab==='settings' && user.is_admin && <Settings/>}
      {tab==='users' && user.is_admin && <AdminUsers/>}
    </div>
  );
}
