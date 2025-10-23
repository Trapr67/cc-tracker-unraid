import React from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';

export default function CalendarView({statuses}){
  const tileContent = ({date, view}) => {
    if(view!=='month') return null;
    const day = date.getDate();
    const matches = statuses.filter(s=> s.due_day === day);
    if(matches.length===0) return null;
    return (<div style={{marginTop:6}}>
      {matches.map(m=> <div key={m.id} style={{fontSize:10, background:m.color, color:'#fff', borderRadius:4, padding:'2px 4px', marginBottom:2, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{m.name} ****{m.last4}</div>)}
    </div>);
  };
  return (<div className='card'>
    <h3>Calendar</h3>
    <Calendar tileContent={tileContent}/>
  </div>);
}
