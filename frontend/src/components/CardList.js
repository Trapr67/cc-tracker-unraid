import React, {useEffect, useState} from 'react';
import { getCards, addCard, updateCard, deleteCard } from '../api';

export default function CardList({refresh, statuses}){
  const [cards,setCards]=useState([]);
  const [form,setForm]=useState({name:'',last4:'',due_day:1,notes:''});
  const [sortBy,setSortBy]=useState('due');

  useEffect(()=>{ load(); },[]);
  async function load(){ const r = await getCards(); setCards(r); }

  async function create(e){ e.preventDefault(); await addCard(form); setForm({name:'',last4:'',due_day:1,notes:''}); await load(); refresh&&refresh(); }
  async function togglePaid(c){ await updateCard(c.id,{paid:!c.paid}); await load(); refresh&&refresh(); }
  async function remove(id){ if(!confirm('Delete?')) return; await deleteCard(id); await load(); refresh&&refresh(); }

  function statusColor(c){
    const today = new Date(); const year=today.getFullYear(); const month=today.getMonth();
    const due = new Date(year, month, c.due_day);
    if(c.paid) return 'green';
    const diff = Math.ceil((due - today)/(1000*60*60*24));
    if(diff<=0) return 'red'; if(diff<=5) return 'yellow'; return 'white';
  }

  const sorted = [...cards].sort((a,b)=> sortBy==='name' ? a.name.localeCompare(b.name) : a.due_day-b.due_day);

  return (<div className='card'>
    <h3>Cards</h3>
    <form onSubmit={create} style={{display:'flex',gap:8,flexWrap:'wrap'}}>
      <input placeholder='name' value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required/>
      <input placeholder='last4' maxLength={4} value={form.last4} onChange={e=>setForm({...form,last4:e.target.value})} required/>
      <input type='number' min={1} max={31} value={form.due_day} onChange={e=>setForm({...form,due_day:Number(e.target.value)})} required/>
      <input placeholder='notes' value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/>
      <button>Add</button>
      <label style={{marginLeft:'auto'}}>Sort:
        <select value={sortBy} onChange={e=>setSortBy(e.target.value)}><option value='due'>Due</option><option value='name'>Name</option></select>
      </label>
    </form>
    <table><thead><tr><th>Name</th><th>Last4</th><th>Due</th><th>Paid</th><th>Notes</th><th></th></tr></thead>
      <tbody>
        {sorted.map(c => (
          <tr key={c.id} style={{background: statusColor(c)==='white'?'#071028': statusColor(c)==='yellow'?'#5a5100': statusColor(c)==='red'?'#5a0f0f':'#0b5a20'}}>
            <td>{c.name}</td>
            <td>****{c.last4}</td>
            <td>{c.due_day}</td>
            <td style={{textAlign:'center'}}><input type='checkbox' checked={c.paid} onChange={()=>togglePaid(c)}/></td>
            <td>{c.notes}</td>
            <td><button onClick={()=>remove(c.id)}>Delete</button></td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>);
}
