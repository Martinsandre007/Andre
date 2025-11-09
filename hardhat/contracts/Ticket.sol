// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EventTicketing {
    struct Event {
        address organizer;
        string name;
        uint256 ticketPrice;
        uint256 totalTickets;
        uint256 soldTickets;
        mapping(address => uint256) ticketsOwned;
    }

    uint256 public nextEventId;
    mapping(uint256 => Event) public events;

    function createEvent(string memory _name, uint256 _ticketPrice, uint256 _totalTickets) external {
        Event storage newEvent = events[nextEventId];
        newEvent.organizer = msg.sender;
        newEvent.name = _name;
        newEvent.ticketPrice = _ticketPrice;
        newEvent.totalTickets = _totalTickets;
        // soldTickets is 0 by default, but it's good to be explicit
        newEvent.soldTickets = 0;
        nextEventId++;
    }

    function buyTickets(uint256 _eventId, uint256 _quantity) external payable {
        Event storage _event = events[_eventId];
        require(msg.value == _event.ticketPrice * _quantity, "Incorrect amount of ether sent");
        require(_event.soldTickets + _quantity <= _event.totalTickets, "Not enough tickets available");

        _event.soldTickets += _quantity;
        _event.ticketsOwned[msg.sender] += _quantity;
    }

    function getMyTickets(uint256 _eventId) external view returns (uint256) {
        return events[_eventId].ticketsOwned[msg.sender];
    }
}
