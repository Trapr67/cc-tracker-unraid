import React, {useEffect, useState} from 'react';
import { listUsers, addUser, modifyUser, deleteUser } from '../api';

export default function AdminUsers(){
  const [users,setUsers]=useState([]);
  const [form,setForm]=useState({username:'',password:'',is_admin:false});
  useEffect(()=>{ load(); },[]);
  async function load(){ setUsers(await listUsers()); }
  async function create(e){ e.preventDefault(); await addUser(form); setForm({username:'',password:'',is_admin:false}); await load(); }
  async function del(id){ if(!confirm('Delete user?')) return; await deleteUser(id); await load(); }
  async function toggleAdmin(u){ await modifyUser(u.id, {is_admin:!u.is_admin}); await load(); }
  return (<div className='card'>
    <h3>User Management</h3>
    <form onSubmit={create} style={{display:'flex',gap:8,flexWrap:'wrap'}}>
      <input placeholder='username' value={form.username} onChange={e=>setForm({...form,username:e.target.value})} required/>
      <input type='password' placeholder='password' value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required/>
      <label style={{display:'flex',alignItems:'center',gap:6}}><input type='checkbox' checked={form.is_admin} onChange={e=>setForm({...form,is_admin:e.target.checked})}/> Admin</label>
      <button>Add user</button>
    </form>
    <table><thead><tr><th>Username</th><th>Admin</th><th>Created</th><th></th></tr></thead><tbody>
      {users.map(u=>(<tr key={u.id}><td>{u.username}</td><td style={{textAlign:'center'}}><input type='checkbox' checked={u.is_admin} onChange={()=>toggleAdmin(u)}/></td><td>{u.created_at}</td><td><button onClick={()=>del(u.id)}>Delete</button></td></tr>))}
    </tbody></table>
  </div>);
}
