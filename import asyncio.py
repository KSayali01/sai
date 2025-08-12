import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime
import time

# Delay helper
async def wait(ms=800):
    await asyncio.sleep(ms / 1000)

# Current timestamp
def get_current_date():
    now = datetime.now()
    return now.strftime("%d%m%y%H%M%S")

# Extract data from the business details page
async def get_page_data(page):
    results = []
    try:
        anchor_links = await page.query_selector_all("a.rllt__link")
        for link in anchor_links:
            await link.click()
            await wait(10000)  # wait for details to load

            try:
                await page.wait_for_selector("g-sticky-content-container", timeout=60000)
            except:
                continue

            data = await page.evaluate("""
                () => {
                    let CName = "", Category = "", Address = "", Rating = "0", Review = "0", MobileNumber = "";
                    
                    const CNameEl = document.querySelector("g-sticky-content-container h2");
                    if (CNameEl) {
                        CName = CNameEl.textContent.split("\\n")[0];
                    }

                    const CategoryEl = document.querySelector(".rllt__details > div:nth-child(2)");
                    if (CategoryEl) {
                        Category = CategoryEl.textContent.replace("Category:", "");
                    }

                    const AddressEl = document.querySelector('g-flippy-carousel div[lang="en-IN"]:nth-child(2)');
                    if (AddressEl) {
                        Address = AddressEl.textContent.replace("Address:", "");
                    }

                    const RatingEl = document.querySelector(".TLYLSe.MaBy9 .CJQ04 .NdWbqe.Y0A0hc .yi40Hd.YrbPuc");
                    if (RatingEl) {
                        Rating = RatingEl.textContent;
                    }

                    const ReviewEl = document.querySelector(".TLYLSe.MaBy9 .CJQ04 .NdWbqe.Y0A0hc .RDApEe.YrbPuc");
                    if (ReviewEl) {
                        Review = ReviewEl.textContent.replace(/[^\\d]/g, "");
                    }

                    const MobileEl = document.querySelector('g-flippy-carousel div[lang="en-IN"] span[aria-label]');
                    if (MobileEl) {
                        MobileNumber = MobileEl.textContent.replace("Phone:", "");
                    }

                    return {CompanyName: CName, Category, Address, Rating, Review, MobileNumber};
                }
            """)
            results.append(data)
        return results
    except Exception as e:
        print("Error in get_page_data:", e)
        return []

# Main function
async def main():
    Service = "Electrician"
    Pincodes = []
    seen_data = set()

    filename = f"{Service}_{get_current_date()}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["CompanyName", "Address", "MobileNumber", "Category", "Rating", "Review", "Pincode"])

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1000, "height": 600})

            for pincode in Pincodes:
                record = 0
                has_next_page = True

                while has_next_page:
                    url = f"https://www.google.com/search?q={Service}+in+{pincode}&tbm=lcl&start={record}"
                    print("URL:", url)
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=60000)
                    except Exception as e:
                        print("Navigation error:", e)
                        continue

                    data = await get_page_data(page)
                    for row in data:
                        unique_id = f"{row['CompanyName']}-{row['Address']}-{pincode}"
                        if unique_id not in seen_data:
                            writer.writerow([
                                row.get("CompanyName", ""),
                                row.get("Address", ""),
                                row.get("MobileNumber", ""),
                                row.get("Category", ""),
                                row.get("Rating", ""),
                                row.get("Review", ""),
                                pincode
                            ])
                            seen_data.add(unique_id)

                    # Check for next page
                    next_button = await page.query_selector("#pnnext")
                    if next_button:
                        await next_button.click()
                        await wait(3000)
                        record += 20
                    else:
                        has_next_page = False

            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())