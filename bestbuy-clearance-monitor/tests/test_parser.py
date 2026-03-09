from src.parser import (
    normalize_online_availability,
    normalize_pickup_availability,
    parse_product_page,
)


def test_normalize_online_availability() -> None:
    assert normalize_online_availability("Available to ship") == "available_online"
    assert normalize_online_availability("Sold out online") == "sold_out_online"
    assert (
        normalize_online_availability("Not available for delivery")
        == "not_available_for_delivery"
    )
    assert normalize_online_availability("Delivery not available") == "not_available_for_delivery"


def test_normalize_pickup_availability() -> None:
    assert normalize_pickup_availability("Ready for pickup tomorrow") == "available_for_pickup"
    assert (
        normalize_pickup_availability("Not available for pickup")
        == "not_available_for_pickup"
    )
    assert normalize_pickup_availability("Pick up unavailable") == "not_available_for_pickup"


def test_parse_product_page_from_json_ld() -> None:
    html = """
    <html>
      <head>
        <script type=\"application/ld+json\">{
          \"@type\": \"Product\",
          \"name\": \"Gaming Desktop X\",
          \"sku\": \"111222\",
          \"brand\": {\"name\": \"BrandA\"},
          \"offers\": [{\"price\": \"1499.99\"}]
        }</script>
      </head>
      <body>
        <div>Available to ship</div>
        <div>Available for pickup</div>
        <div>Processor: Intel Core i7</div>
        <div>RAM: 32GB</div>
        <div>Storage: 1TB SSD</div>
        <div>Graphics: RTX 4070</div>
      </body>
    </html>
    """
    parsed = parse_product_page("https://example.com/p/1", html)

    assert parsed["name"] == "Gaming Desktop X"
    assert parsed["price"] == "1499.99"
    assert parsed["sku"] == "111222"
    assert parsed["online_availability"] == "available_online"
    assert parsed["pickup_availability"] == "available_for_pickup"


def test_parse_product_page_sku_falls_back_to_web_code_text() -> None:
    html = """
    <html>
      <head><title>Product A</title></head>
      <body>
        <div>Web Code: 98765432</div>
        <div>Delivery unavailable in your area</div>
        <div>Pickup unavailable at nearby stores</div>
      </body>
    </html>
    """

    parsed = parse_product_page("https://example.com/p/2", html)

    assert parsed["sku"] == "98765432"
    assert parsed["online_availability"] == "not_available_for_delivery"
    assert parsed["pickup_availability"] == "not_available_for_pickup"
