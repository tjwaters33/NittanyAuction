function makeProductCard(prod){
    const seller = prod.vendor_name?prod.vendor_name: prod.seller_email;
    const card = document.createElement('div');
    card.className = 'card';
    card.style.width = '15rem';
    card.innerHTML = `
        <div class="card-body p-3 d-flex flex-column">
            <h6 class="card-title fw-semibold mb-1">${prod.auction_title}</h6>
            <p class="card-text small mb-1">${prod.product_name}</p>
            <p class="card-text text-muted small mb-0">${prod.product_description}</p>
            <div class="col p-0">
                <div class="row mt-2">
                    <div class="col-5 pr-1">
                        <p class="fw-medium mb-0">$${prod.reserve_price.toFixed(2)}</p>
                    </div>
                    <div class="col-4 pr-1 pl-0">
                        <p class="mb-0">${prod.max_bids} bids</p>
                    </div>
                    <div class="col-3 pl-0">
                        <p class="mb-0">${prod.quantity} qty</p>
                    </div>
                </div>
                <div class="row mt-1 mb-2">
                    <div class="col">
                        <p class="small mb-0">${seller}</p>
                    </div>
                </div>
            </div>

            <a href="/listings/${prod.listing_id}" class="btn btn-primary mt-auto btn-sm w-100">View listing</a>
        </div>
    `;
    return card;
}