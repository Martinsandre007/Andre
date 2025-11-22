// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./NFTCollectible.sol";

contract EventTicketing is Ownable {
    struct Event {
        address organizer;
        string name;
        uint256 basePrice;
        uint256 totalTickets;
        uint256 soldTickets;
        uint256 maxTicketsPerWallet;
        bool isCancelled;
        mapping(address => uint256) ticketsOwned;
        mapping(address => bool) hasRefunded;
    }

    struct GroupBuy {
        uint256 eventId;
        address initiator;
        uint256 totalAmountNeeded;
        uint256 currentAmount;
        bool active;
        address[] contributors;
        mapping(address => uint256) contributions;
    }

    struct ResaleItem {
        uint256 resaleId;
        uint256 eventId;
        address seller;
        uint256 price;
        bool active;
    }

    uint256 public nextEventId;
    uint256 public nextGroupBuyId;
    uint256 public nextResaleId;
    mapping(uint256 => Event) public events;
    mapping(uint256 => GroupBuy) public groupBuys;
    mapping(uint256 => ResaleItem) public resaleItems;
    
    mapping(address => bool) public verifiedMembers;
    uint256 public constant VERIFIED_DISCOUNT_PERCENT = 10; // 10% discount
    
    NFTCollectible public nftContract;

    event TicketSold(uint256 indexed eventId, address indexed buyer, uint256 price, uint256 timestamp);
    event GroupBuyInitiated(uint256 indexed groupBuyId, uint256 indexed eventId, address initiator);
    event GroupBuyContributed(uint256 indexed groupBuyId, address contributor, uint256 amount);
    event GroupBuyCompleted(uint256 indexed groupBuyId, uint256 indexed eventId);
    event MemberVerified(address indexed member);
    event EventCancelled(uint256 indexed eventId);
    event RefundClaimed(uint256 indexed eventId, address indexed buyer, uint256 amount);
    event TicketListedForResale(uint256 indexed resaleId, uint256 indexed eventId, address seller, uint256 price);
    event ResaleTicketSold(uint256 indexed resaleId, uint256 indexed eventId, address buyer, address seller, uint256 price);

    constructor(address _nftContractAddress) {
        nftContract = NFTCollectible(_nftContractAddress);
    }

    function verifyMember(address _member) external onlyOwner {
        verifiedMembers[_member] = true;
        emit MemberVerified(_member);
    }

    function createEvent(string memory _name, uint256 _basePrice, uint256 _totalTickets, uint256 _maxTicketsPerWallet) external {
        Event storage newEvent = events[nextEventId];
        newEvent.organizer = msg.sender;
        newEvent.name = _name;
        newEvent.basePrice = _basePrice;
        newEvent.totalTickets = _totalTickets;
        newEvent.soldTickets = 0;
        newEvent.maxTicketsPerWallet = _maxTicketsPerWallet;
        newEvent.isCancelled = false;
        nextEventId++;
    }

    function getPrice(uint256 _eventId) public view returns (uint256) {
        Event storage _event = events[_eventId];
        if (_event.totalTickets == 0) return _event.basePrice;
        
        // Linear price increase: Base Price + (Base Price * (Sold / Total))
        uint256 increase = (_event.basePrice * _event.soldTickets) / _event.totalTickets;
        return _event.basePrice + increase;
    }

    function getDiscountedPrice(uint256 _eventId, address _buyer) public view returns (uint256) {
        uint256 currentPrice = getPrice(_eventId);
        if (verifiedMembers[_buyer]) {
            return currentPrice - ((currentPrice * VERIFIED_DISCOUNT_PERCENT) / 100);
        }
        return currentPrice;
    }

    function buyTickets(uint256 _eventId, uint256 _quantity) external payable {
        Event storage _event = events[_eventId];
        require(!_event.isCancelled, "Event is cancelled");
        uint256 unitPrice = getDiscountedPrice(_eventId, msg.sender);
        uint256 totalCost = unitPrice * _quantity;

        require(msg.value >= totalCost, "Incorrect amount of ether sent");
        require(_event.soldTickets + _quantity <= _event.totalTickets, "Not enough tickets available");
        require(_event.ticketsOwned[msg.sender] + _quantity <= _event.maxTicketsPerWallet, "Exceeds max tickets per wallet");

        _event.soldTickets += _quantity;
        _event.ticketsOwned[msg.sender] += _quantity;
        
        // Mint NFT for each ticket
        for(uint256 i = 0; i < _quantity; i++) {
            nftContract.mintCollectible(msg.sender, _eventId);
        }

        emit TicketSold(_eventId, msg.sender, unitPrice, block.timestamp);
    }

    function initiateGroupBuy(uint256 _eventId) external {
        // Group buy uses the initiator's price (so if they are verified, the group gets the discount)
        uint256 currentPrice = getDiscountedPrice(_eventId, msg.sender);
        
        GroupBuy storage newGroupBuy = groupBuys[nextGroupBuyId];
        newGroupBuy.eventId = _eventId;
        newGroupBuy.initiator = msg.sender;
        newGroupBuy.totalAmountNeeded = currentPrice;
        newGroupBuy.currentAmount = 0;
        newGroupBuy.active = true;
        
        nextGroupBuyId++;
        
        emit GroupBuyInitiated(nextGroupBuyId - 1, _eventId, msg.sender);
    }

    function contributeToGroupBuy(uint256 _groupBuyId) external payable {
        GroupBuy storage groupBuy = groupBuys[_groupBuyId];
        require(groupBuy.active, "Group buy is not active");
        require(groupBuy.currentAmount + msg.value <= groupBuy.totalAmountNeeded, "Amount exceeds needed total");

        groupBuy.contributions[msg.sender] += msg.value;
        groupBuy.currentAmount += msg.value;
        groupBuy.contributors.push(msg.sender);

        emit GroupBuyContributed(_groupBuyId, msg.sender, msg.value);

        if (groupBuy.currentAmount == groupBuy.totalAmountNeeded) {
            _finalizeGroupBuy(_groupBuyId);
        }
    }

    function _finalizeGroupBuy(uint256 _groupBuyId) internal {
        GroupBuy storage groupBuy = groupBuys[_groupBuyId];
        groupBuy.active = false;
        
        Event storage _event = events[groupBuy.eventId];
        _event.soldTickets += 1;
        _event.ticketsOwned[groupBuy.initiator] += 1; // Ticket goes to initiator
        
        nftContract.mintCollectible(groupBuy.initiator, groupBuy.eventId);
        
        emit GroupBuyCompleted(_groupBuyId, groupBuy.eventId);
        emit TicketSold(groupBuy.eventId, groupBuy.initiator, groupBuy.totalAmountNeeded, block.timestamp);
    }

    function cancelEvent(uint256 _eventId) external {
        Event storage _event = events[_eventId];
        require(msg.sender == _event.organizer, "Only organizer can cancel");
        _event.isCancelled = true;
        emit EventCancelled(_eventId);
    }

    function claimRefund(uint256 _eventId) external {
        Event storage _event = events[_eventId];
        require(_event.isCancelled, "Event is not cancelled");
        require(_event.ticketsOwned[msg.sender] > 0, "No tickets to refund");
        require(!_event.hasRefunded[msg.sender], "Already refunded");

        uint256 refundAmount = _event.ticketsOwned[msg.sender] * _event.basePrice;
        _event.hasRefunded[msg.sender] = true;
        _event.ticketsOwned[msg.sender] = 0;

        payable(msg.sender).transfer(refundAmount);
        emit RefundClaimed(_eventId, msg.sender, refundAmount);
    }

    function listTicketForResale(uint256 _eventId, uint256 _price) external {
        Event storage _event = events[_eventId];
        require(_event.ticketsOwned[msg.sender] > 0, "No tickets to sell");
        
        _event.ticketsOwned[msg.sender] -= 1; // Lock ticket

        ResaleItem storage item = resaleItems[nextResaleId];
        item.resaleId = nextResaleId;
        item.eventId = _eventId;
        item.seller = msg.sender;
        item.price = _price;
        item.active = true;

        emit TicketListedForResale(nextResaleId, _eventId, msg.sender, _price);
        nextResaleId++;
    }

    function buyResaleTicket(uint256 _resaleId) external payable {
        ResaleItem storage item = resaleItems[_resaleId];
        require(item.active, "Item not active");
        require(msg.value >= item.price, "Insufficient funds");

        item.active = false;
        Event storage _event = events[item.eventId];
        
        // 10% Royalty to Organizer
        uint256 royalty = (item.price * 10) / 100;
        uint256 sellerAmount = item.price - royalty;

        _event.ticketsOwned[msg.sender] += 1;

        payable(item.seller).transfer(sellerAmount);
        payable(_event.organizer).transfer(royalty);

        emit ResaleTicketSold(_resaleId, item.eventId, msg.sender, item.seller, item.price);
    }

    function getMyTickets(uint256 _eventId) external view returns (uint256) {
        return events[_eventId].ticketsOwned[msg.sender];
    }
}
