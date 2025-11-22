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
  const [isVerified, setIsVerified] = useState(false);

  const connectWallet = async () => {
    if (window.ethereum) {
      try {
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const contract = new ethers.Contract(contractAddress, EventTicketing.abi, signer);
        const address = await signer.getAddress();

        setProvider(provider);
        setSigner(signer);
        setContract(contract);
        setAccount(address);

        // Check if user is verified
        try {
          const verified = await contract.verifiedMembers(address);
          setIsVerified(verified);
        } catch (e) {
          console.log("Error checking verification status", e);
        }

        fetchEvents(contract, address);
      } catch (error) {
        console.error("Could not connect to wallet", error);
      }
    } else {
      alert("Please install MetaMask!");
    }
  };

  const fetchEvents = async (contractInstance, userAddress) => {
    try {
      const eventCount = await contractInstance.nextEventId();
      const eventsData = [];
      for (let i = 0; i < eventCount; i++) {
        const event = await contractInstance.events(i);

        // Get the price relevant to the user (discounted if verified)
        let price;
        if (userAddress) {
          price = await contractInstance.getDiscountedPrice(i, userAddress);
        } else {
          price = await contractInstance.getPrice(i);
        }

        eventsData.push({
          id: i,
          name: event.name,
          display_price: ethers.formatEther(price),
          base_price: ethers.formatEther(event.basePrice),
          total_tickets: Number(event.totalTickets),
          sold_tickets: Number(event.soldTickets),
        });
      }
      setEvents(eventsData);
    } catch (error) {
      console.error("Could not fetch events", error);
    }
  };

  const buyTicket = async (eventId, price) => {
    if (!contract) return;
    try {
      const tx = await contract.buyTickets(eventId, 1, {
        value: ethers.parseEther(price.toString())
      });
      await tx.wait();
      alert("Ticket purchased successfully!");
      fetchEvents(contract, account);
    } catch (error) {
      console.error("Could not buy ticket", error);
      alert("Error buying ticket: " + (error.reason || error.message));
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Event Ticketing</h1>
        {account ? (
          <div className="glass" style={{ padding: '10px 20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>{account.slice(0, 6)}...{account.slice(-4)}</span>
            {isVerified && <span className="badge badge-available" style={{ marginBottom: 0 }}>Verified Member</span>}
          </div>
        ) : (
          <button className="btn-primary" onClick={connectWallet}>Connect Wallet</button>
        )}
      </header>

      <div className="container">
        <div className="event-list">
          {events.map(event => {
            const isSoldOut = event.sold_tickets >= event.total_tickets;
            return (
              <div key={event.id} className="event-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <span className={`badge ${isSoldOut ? 'badge-soldout' : 'badge-available'}`}>
                    {isSoldOut ? 'Sold Out' : 'Available'}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: #{event.id}</span>
                </div>

                <h2>{event.name}</h2>

                <div className="price-tag">
                  {event.display_price} ETH
                  {isVerified && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: '8px' }}>(Discounted)</span>}
                </div>

                <p>Tickets Left: {event.total_tickets - event.sold_tickets} / {event.total_tickets}</p>

                <div className="card-actions">
                  <button
                    className="btn-primary"
                    onClick={() => buyTicket(event.id, event.display_price)}
                    disabled={isSoldOut}
                    style={{ opacity: isSoldOut ? 0.5 : 1, cursor: isSoldOut ? 'not-allowed' : 'pointer' }}
                  >
                    {isSoldOut ? 'Sold Out' : 'Buy Ticket'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default App;
