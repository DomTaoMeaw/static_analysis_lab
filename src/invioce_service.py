from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple


# -------------------- Data Models --------------------

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False


@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]


# -------------------- Service --------------------

class InvoiceService:

    SHIPPING_RULES = {
        "TH": lambda subtotal: 60 if subtotal < 500 else 0,
        "JP": lambda subtotal: 600 if subtotal < 4000 else 0,
        "US": lambda subtotal: 15 if subtotal < 100 else (8 if subtotal < 300 else 0),
        "DEFAULT": lambda subtotal: 25 if subtotal < 200 else 0,
    }

    TAX_RATE = {
        "TH": 0.07,
        "JP": 0.10,
        "US": 0.08,
        "DEFAULT": 0.05,
    }

    MEMBERSHIP_DISCOUNT = {
        "gold": 0.03,
        "platinum": 0.05,
    }

    COUPON_RATE = {
        "WELCOME10": 0.10,
        "VIP20": 0.20,
        "STUDENT5": 0.05,
    }

    VALID_CATEGORIES = {"book", "food", "electronics", "other"}

    # -------------------- Validation --------------------

    def _validate(self, inv: Invoice) -> None:
        if inv is None:
            raise ValueError("Invoice is missing")

        problems: List[str] = []

        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")

        for item in inv.items:
            if not item.sku:
                problems.append("Item sku is missing")
            if item.qty <= 0:
                problems.append(f"Invalid qty for {item.sku}")
            if item.unit_price < 0:
                problems.append(f"Invalid price for {item.sku}")
            if item.category not in self.VALID_CATEGORIES:
                problems.append(f"Unknown category for {item.sku}")

        if problems:
            raise ValueError("; ".join(problems))

    # -------------------- Calculation Helpers --------------------

    def _calculate_subtotal(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = sum(i.unit_price * i.qty for i in items)
        fragile_fee = sum(5.0 * i.qty for i in items if i.fragile)
        return subtotal, fragile_fee

    def _calculate_shipping(self, country: str, subtotal: float) -> float:
        rule = self.SHIPPING_RULES.get(country, self.SHIPPING_RULES["DEFAULT"])
        return rule(subtotal)

    def _calculate_discount(self, inv: Invoice, subtotal: float) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        discount = 0.0

        # Membership
        if inv.membership in self.MEMBERSHIP_DISCOUNT:
            discount += subtotal * self.MEMBERSHIP_DISCOUNT[inv.membership]
        elif subtotal > 3000:
            discount += 20

        # Coupon
        if inv.coupon:
            code = inv.coupon.strip()
            if code in self.COUPON_RATE:
                discount += subtotal * self.COUPON_RATE[code]
            else:
                warnings.append("Unknown coupon")

        return discount, warnings

    def _calculate_tax(self, country: str, taxable_amount: float) -> float:
        rate = self.TAX_RATE.get(country, self.TAX_RATE["DEFAULT"])
        return taxable_amount * rate

    # -------------------- Public API --------------------

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        self._validate(inv)

        subtotal, fragile_fee = self._calculate_subtotal(inv.items)
        shipping = self._calculate_shipping(inv.country, subtotal)

        discount, warnings = self._calculate_discount(inv, subtotal)
        tax = self._calculate_tax(inv.country, subtotal - discount)

        total = subtotal + shipping + fragile_fee + tax - discount

        if total < 0:
            total = 0

        if subtotal > 10000 and inv.membership not in self.MEMBERSHIP_DISCOUNT:
            warnings.append("Consider membership upgrade")

        return total, warnings
