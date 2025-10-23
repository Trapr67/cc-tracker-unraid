import React, {useEffect, useState} from 'react';
import { getSettings, putSettings } from '../api';

export default function Settings(){
  const [s,setS]=useState(null); const [msg,setMsg]=useState('');
  useEffect(()=>{ (async()=>{ setS(await getSettings()); })(); }, []);
  if(!s) return <div className='card'>Loading settings...</div>;
  async function save(e){ e.preventDefault(); await putSettings(s); setMsg('Saved ✓'); setTimeout(()=>setMsg(''),2000); }
  const set = (k,v)=> setS({...s,[k]:v});
  return (<div className='card'><h3>Notifications</h3>
    <form onSubmit={save} style={{display:'grid',gridTemplateColumns:'1fr 1fr', gap:10}}>
      <label>SMTP Host<input value={s.SMTP_HOST||''} onChange={e=>set('SMTP_HOST',e.target.value)}/></label>
      <label>SMTP Port<input value={s.SMTP_PORT||''} onChange={e=>set('SMTP_PORT',e.target.value)}/></label>
      <label>SMTP User<input value={s.SMTP_USER||''} onChange={e=>set('SMTP_USER',e.target.value)}/></label>
      <label>SMTP Pass<input type='password' value={s.SMTP_PASS||''} onChange={e=>set('SMTP_PASS',e.target.value)}/></label>
      <label>Alert Email<input value={s.ALERT_EMAIL||''} onChange={e=>set('ALERT_EMAIL',e.target.value)}/></label>
      <label>Webhook URL<input value={s.WEBHOOK_URL||''} onChange={e=>set('WEBHOOK_URL',e.target.value)}/></label>
      <label>Twilio SID<input value={s.TWILIO_SID||''} onChange={e=>set('TWILIO_SID',e.target.value)}/></label>
      <label>Twilio Token<input type='password' value={s.TWILIO_TOKEN||''} onChange={e=>set('TWILIO_TOKEN',e.target.value)}/></label>
      <label>Twilio From<input value={s.TWILIO_FROM||''} onChange={e=>set('TWILIO_FROM',e.target.value)}/></label>
      <label>Twilio To<input value={s.TWILIO_TO||''} onChange={e=>set('TWILIO_TO',e.target.value)}/></label>
      <div style={{gridColumn:'1 / -1', display:'flex',gap:8, alignItems:'center'}}>
        <button>Save</button><span>{msg}</span>
      </div>
    </form>
  </div>);
}

