document.addEventListener("DOMContentLoaded", () => {
	const socket = io();
	const orderForm = document.getElementById("order-form");
	const orderType = document.getElementById("orderType");
	const symbolInput = document.getElementById("symbol");
	const limitFields = document.querySelectorAll(".limit-field");
	const stopLimitFields = document.querySelectorAll(".stop-limit-field");
	const connectionStatus = document.getElementById("connection-status");
	const toast = new bootstrap.Toast(document.getElementById("notification-toast"));
	const toastTitle = document.getElementById("toast-title");
	const toastMessage = document.getElementById("toast-message");

	// Tab handling
	const openOrdersTab = document.getElementById("openOrdersTab");
	const recentTradesTab = document.getElementById("recentTradesTab");
	const openOrdersTable = document.getElementById("openOrdersTable");
	const recentTradesTable = document.getElementById("recentTradesTable");

	openOrdersTab.addEventListener("click", () => {
		openOrdersTab.classList.add("active");
		recentTradesTab.classList.remove("active");
		openOrdersTable.style.display = "block";
		recentTradesTable.style.display = "none";
	});

	recentTradesTab.addEventListener("click", () => {
		recentTradesTab.classList.add("active");
		openOrdersTab.classList.remove("active");
		recentTradesTable.style.display = "block";
		openOrdersTable.style.display = "none";
	});

	// Load available symbols
	fetch("/api/symbols")
		.then((response) => response.json())
		.then((symbols) => {
			const datalist = document.createElement("datalist");
			datalist.id = "symbol-list";
			symbols.forEach((symbol) => {
				const option = document.createElement("option");
				option.value = symbol;
				datalist.appendChild(option);
			});
			document.body.appendChild(datalist);
			symbolInput.setAttribute("list", "symbol-list");
		})
		.catch((error) => console.error("Error loading symbols:", error));

	// Socket connection handling
	socket.on("connect", () => {
		connectionStatus.innerHTML = '<span class="badge bg-success">Connected</span>';
		showNotification("Connection Status", "Connected to server successfully!", "success");
		// Request initial data
		socket.emit("get_balance");
		socket.emit("get_open_orders");
	});

	socket.on("disconnect", () => {
		connectionStatus.innerHTML = '<span class="badge bg-danger">Disconnected</span>';
		showNotification("Connection Status", "Disconnected from server!", "error");
	});

	// Handle order type changes
	orderType.addEventListener("change", () => {
		const selectedType = orderType.value;
		limitFields.forEach((field) => {
			field.style.display = selectedType === "LIMIT" || selectedType === "STOP_LIMIT" ? "block" : "none";
			field.querySelector("input").required = selectedType === "LIMIT" || selectedType === "STOP_LIMIT";
		});
		stopLimitFields.forEach((field) => {
			field.style.display = selectedType === "STOP_LIMIT" ? "block" : "none";
			field.querySelector("input").required = selectedType === "STOP_LIMIT";
		});
	});

	// Handle form submission
	orderForm.addEventListener("submit", (e) => {
		e.preventDefault();
		const submitButton = orderForm.querySelector('button[type="submit"]');
		submitButton.disabled = true;
		submitButton.innerHTML = '<div class="loading-spinner"></div>';

		const formData = {
			symbol: document.getElementById("symbol").value.toUpperCase(),
			type: orderType.value,
			side: document.getElementById("side").value,
			quantity: parseFloat(document.getElementById("quantity").value),
		};

		if (formData.type === "LIMIT" || formData.type === "STOP_LIMIT") {
			formData.price = parseFloat(document.getElementById("price").value);
		}

		if (formData.type === "STOP_LIMIT") {
			formData.stopPrice = parseFloat(document.getElementById("stopPrice").value);
		}

		socket.emit("place_order", formData);
	});

	// Handle balance updates
	socket.on("balance_update", (balances) => {
		const balanceBody = document.getElementById("balance-body");
		balanceBody.innerHTML = "";

		Object.entries(balances)
			.sort(([assetA], [assetB]) => assetA.localeCompare(assetB))
			.forEach(([asset, balance]) => {
				const row = document.createElement("tr");
				row.innerHTML = `
					<td>${asset}</td>
					<td>${parseFloat(balance.free).toFixed(8)}</td>
					<td>${parseFloat(balance.locked).toFixed(8)}</td>
				`;
				balanceBody.appendChild(row);
			});
	});

	// Handle open orders updates
	socket.on("open_orders_update", (orders) => {
		const ordersBody = document.getElementById("orders-body");
		ordersBody.innerHTML = "";

		if (orders.length === 0) {
			const row = document.createElement("tr");
			row.innerHTML = `
				<td colspan="9" class="text-center text-muted">
					No open orders
				</td>
			`;
			ordersBody.appendChild(row);
			return;
		}

		orders.forEach((order) => {
			const row = document.createElement("tr");
			row.innerHTML = `
				<td>${order.time}</td>
				<td>${order.symbol}</td>
				<td><span class="badge bg-info">${order.type}</span></td>
				<td>
					<span class="badge ${order.side === "BUY" ? "bg-success" : "bg-danger"}">
						${order.side}
					</span>
				</td>
				<td>${parseFloat(order.price).toFixed(8)}</td>
				<td>${parseFloat(order.origQty).toFixed(8)}</td>
				<td>${parseFloat(order.executedQty).toFixed(8)}</td>
				<td><span class="badge bg-secondary">${order.status}</span></td>
				<td>
					<button class="btn btn-danger btn-sm" onclick="cancelOrder('${order.symbol}', ${order.orderId})">
						Cancel
					</button>
				</td>
			`;
			ordersBody.appendChild(row);
		});
	});

	// Handle recent trades updates
	socket.on("recent_trades_update", (trades) => {
		const tradesBody = document.getElementById("trades-body");
		tradesBody.innerHTML = "";

		if (trades.length === 0) {
			const row = document.createElement("tr");
			row.innerHTML = `
				<td colspan="7" class="text-center text-muted">
					No recent trades
				</td>
			`;
			tradesBody.appendChild(row);
			return;
		}

		trades.forEach((trade) => {
			const row = document.createElement("tr");
			row.innerHTML = `
				<td>${trade.time}</td>
				<td>${trade.symbol}</td>
				<td>
					<span class="badge ${trade.isBuyer ? "bg-success" : "bg-danger"}">
						${trade.isBuyer ? "BUY" : "SELL"}
					</span>
				</td>
				<td>${parseFloat(trade.price).toFixed(8)}</td>
				<td>${parseFloat(trade.qty).toFixed(8)}</td>
				<td>${parseFloat(trade.quoteQty).toFixed(8)}</td>
				<td>${parseFloat(trade.commission).toFixed(8)} ${trade.commissionAsset}</td>
			`;
			tradesBody.appendChild(row);
		});

		// Switch to recent trades tab for market orders
		recentTradesTab.click();
	});

	// Handle order placement response
	socket.on("order_response", (response) => {
		const submitButton = orderForm.querySelector('button[type="submit"]');
		submitButton.disabled = false;
		submitButton.innerHTML = "Place Order";

		if (response.success) {
			showNotification("Order Placed", "Order placed successfully!", "success");
			orderForm.reset();
		} else {
			showNotification("Order Error", response.error, "error");
		}
	});

	// Handle order cancellation response
	socket.on("cancel_response", (response) => {
		if (response.success) {
			showNotification("Order Cancelled", "Order cancelled successfully!", "success");
		} else {
			showNotification("Cancellation Error", response.error, "error");
		}
	});

	// Utility function to show notifications
	function showNotification(title, message, type) {
		toastTitle.textContent = title;
		toastMessage.textContent = message;
		const toastElement = document.getElementById("notification-toast");

		// Remove existing color classes
		toastElement.classList.remove("bg-success", "bg-danger", "bg-warning");

		// Add appropriate color class
		switch (type) {
			case "success":
				toastElement.classList.add("bg-success");
				break;
			case "error":
				toastElement.classList.add("bg-danger");
				break;
			default:
				toastElement.classList.add("bg-warning");
		}

		toast.show();
	}
});

// Global function to cancel orders
function cancelOrder(symbol, orderId) {
	const socket = io();
	socket.emit("cancel_order", { symbol, orderId });
}
