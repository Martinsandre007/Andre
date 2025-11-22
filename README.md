# Decentralized Event Ticketing System

This project is a decentralized event ticketing system built for the BlockDAG buildathon. It uses a smart contract to manage events and ticket sales, and a React frontend to interact with the contract.

## Setup

1.  **Install Dependencies:**
    *   `npm install -g serve`
    *   `cd hardhat && npm install`
    *   `cd frontend && npm install`
    *   `python3 -m pip install --user Flask`

2.  **Deploy the Smart Contract:**
    *   `./deploy.sh`
    *   This will start a local Hardhat node and deploy the `EventTicketing` smart contract. The contract address will be printed to the console.

3.  **Update the Contract Address:**
    *   Open `frontend/src/App.js` and replace the `contractAddress` with the address from the previous step.

4.  **Run the Frontend:**
    *   `cd frontend && npm run build`
    *   `serve -s build -l 3000`
    *   The application will be available at `http://localhost:3000`.

## Usage

1.  Open the application in your browser.
2.  Connect your MetaMask wallet.
3.  You will see a list of events.
4.  Click the "Buy Ticket" button to purchase a ticket.
