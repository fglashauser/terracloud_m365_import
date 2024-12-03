from .factory_base import FactoryBase
import frappe
from .order import Order, PriceType

class SubscriptionPlanFactory(FactoryBase):

    def create_from_orders(self, orders: list[Order]) -> list[Order]:
        """
        Erstellt Subscription-Pläne aus einer Liste von Bestellungen.
        Stellt eine Zuordnung zwischen Bestellung und Subscription-Plan her.

        Args:
            orders (list[Order]): Die Liste der Bestellungen.

        Returns:
            list[Order]: Die Liste der Bestellungen mit zugeordneten Subscription-Plänen.
        """
        mapped_orders = []

        for order in orders:

            # Neuen Subscription Plan erstellen
            doc = frappe.get_doc({
                'doctype': 'Subscription Plan',
                'plan_name': f'M365 {order.customer_no} {order.order_no}',
                'seller_orderno': order.order_no,
                'customer': order.customer_no,
                'price_determination': 'Based On Price List',
                'price_list': self.settings.price_list,
                'item': order.article_no,
                'terracloud_start_date': order.start_date,
                'billing_interval': 'Year' if order.price_type == PriceType.YEARLY \
                    else 'Month'
            }).insert()

            # Mapping zwischen Bestellung und Subscription-Plan herstellen
            order.map_subscription_plan(doc)
            mapped_orders.append(order)
 
        frappe.db.commit()

        return mapped_orders