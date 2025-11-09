import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import './App.css';
import EventTicketing from './EventTicketing.json'; // The ABI

const contractAddress = "YOUR_CONTRACT_ADDRESS"; // Placeholder

function App() {
  const [provider, setProvider] = useState(null);
  const [signer, setSigner] = useState(null);
  const [contract, setContract] = useState(null);
  const [account, setAccount] = useState(null);
  const [events, setEvents] = useState([]);

  const connectWallet = async () => {
    if (window.ethereum) {
      try {
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const contract = new ethers.Contract(contractAddress, EventTicketing.abi, signer);

        setProvider(provider);
        setSigner(signer);
        setContract(contract);
        setAccount(await signer.getAddress());

        fetchEvents(contract);
      } catch (error) {
        console.error("Could not connect to wallet", error);
      }
    } else {
      alert("Please install MetaMask!");
    }
  };

  const fetchEvents = async (contractInstance) => {
    try {
      const eventCount = await contractInstance.nextEventId();
      const events = [];
      for (let i = 0; i < eventCount; i++) {
        const event = await contractInstance.events(i);
        events.push({
          id: i,
          name: event.name,
          ticket_price: ethers.formatEther(event.ticketPrice),
          total_tickets: Number(event.totalTickets),
          sold_tickets: Number(event.soldTickets),
        });
      }
      setEvents(events);
    } catch (error) {
      console.error("Could not fetch events", error);
    }
  };

  const buyTicket = async (eventId, price) => {
    try {
      const tx = await contract.buyTickets(eventId, 1, {
        value: ethers.parseEther(price.toString())
      });
      await tx.wait();
      alert("Ticket purchased successfully!");
      fetchEvents(contract);
    } catch (error) {
      console.error("Could not buy ticket", error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Event Ticketing</h1>
        {account ? (
          <p>Connected: {account}</p>
        ) : (
          <button onClick={connectWallet}>Connect Wallet</button>
        )}
      </header>
      <div className="event-list">
        {events.map(event => (
          <div key={event.id} className="event-card">
            <h2>{event.name}</h2>
            <p>Price: {event.ticket_price} ETH</p>
            <p>Tickets Left: {event.total_tickets - event.sold_tickets}</p>
            <button onClick={() => buyTicket(event.id, event.ticket_price)}>Buy Ticket</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
