const WA_NUMBER = "6282233262629";

// GANTI URL gambar di bawah dengan link foto asli dari Instagram @tysa.dessert / @segokolet
// Cara: buka IG di browser > klik foto > klik kanan Copy image address > paste di field img
const products = [
  {
    id: 1,
    name: "Salad Buah Premium",
    price: 25000,
    cat: "salad",
    img: "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=500&auto=format&fit=crop&q=60",
    desc: "Buah segar apel, anggur, melon, jelly + creamy keju lumer 300ml",
    badge: "Best Seller"
  },
  {
    id: 2,
    name: "Salad Sayur (Veggie Salad)",
    price: 22000,
    cat: "salad",
    img: "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&auto=format&fit=crop&q=60",
    desc: "Sayuran fresh + dressing mayo wijen, sehat & mengenyangkan",
    badge: "Healthy"
  },
  {
    id: 3,
    name: "Asinan Buah Segar",
    price: 20000,
    cat: "segar",
    img: "https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=500&auto=format&fit=crop&q=60",
    desc: "Mangga, kedondong, jambu + kuah asinan pedas manis segar",
    badge: "Pedas Segar"
  },
  {
    id: 4,
    name: "Puding Tysa Lumer",
    price: 15000,
    cat: "segar",
    img: "https://images.unsplash.com/photo-1488477181946-64290103bb53?w=500&auto=format&fit=crop&q=60",
    desc: "Puding susu lembut + vla vanila, varian coklat / stroberi / matcha",
    badge: null
  },
  {
    id: 5,
    name: "Sop Buah Tropical",
    price: 18000,
    cat: "segar",
    img: "https://images.unsplash.com/photo-1543528171-82ad35286012?w=500&auto=format&fit=crop&q=60",
    desc: "Buah potong + kuah susu segar + nata de coco, dingin lebih nikmat",
    badge: null
  },
  {
    id: 6,
    name: "Kimbab",
    price: 20000,
    cat: "nasi",
    img: "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=500&auto=format&fit=crop&q=60",
    desc: "Kimbab nori isi ayam, telur, sayur mayo - isi 8 potong",
    badge: ""
  },
  {
    id: 7,
    name: "Nasi Kulit Segokolet",
    price: 15000,
    cat: "nasi",
    img: "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500&auto=format&fit=crop&q=60",
    desc: "Nasi hangat + kulit ayam crispy sambal korek + lalap",
    badge: "Gurih Pedas"
  },
];

let cart = {};
let currentFilter="all";

function formatRp(n){ return "Rp " + n.toLocaleString("id-ID"); }

function render(){
  const grid=document.getElementById("productGrid");
  const filtered = currentFilter==="all" ? products : products.filter(p=>p.cat===currentFilter);
  grid.innerHTML = filtered.map(p=>{
    const qty = cart[p.id]||0;
    return `<div class="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition flex flex-col">
      <div class="relative">
        <img src="${p.img}" class="w-full h-48 object-cover" loading="lazy" alt="${p.name}">
        ${p.badge?`<span class="absolute top-3 left-3 bg-primary text-white text-xs font-bold px-2 py-1 rounded-full">${p.badge}</span>`:""}
        <span class="absolute top-3 right-3 bg-white/90 text-xs font-semibold px-2 py-1 rounded-full capitalize">${p.cat}</span>
      </div>
      <div class="p-4 flex-1 flex flex-col">
        <h3 class="font-bold text-sm leading-tight">${p.name}</h3>
        <p class="text-xs text-gray-500 mt-1 flex-1">${p.desc}</p>
        <p class="font-bold text-primary mt-3">${formatRp(p.price)}</p>
        <div class="mt-3 flex gap-2">
          ${qty===0
            ?`<button onclick="addToCart(${p.id})" class="flex-1 bg-secondary text-white py-2 rounded-full text-sm font-semibold hover:bg-[#4A1142]"><i class='fa-solid fa-cart-plus mr-1'></i> Tambah</button>`
            :`<div class="flex-1 flex items-center justify-between bg-softpink border border-pink-200 rounded-full px-2 py-1">
                <button onclick="changeQty(${p.id},-1)" class="w-8 h-8 bg-white rounded-full shadow text-sm">−</button>
                <span class="font-bold text-sm">${qty} x</span>
                <button onclick="changeQty(${p.id},1)" class="w-8 h-8 bg-primary text-white rounded-full text-sm">+</button>
             </div>`
          }
          <button onclick="pesanSatuan(${p.id})" class="border px-3 py-2 rounded-full text-xs font-semibold hover:bg-gray-50">WA</button>
        </div>
      </div>
    </div>`
  }).join("");
  updateCartBar();
}

function addToCart(id){ cart[id]=(cart[id]||0)+1; render(); }
function changeQty(id, delta){
  cart[id]=(cart[id]||0)+delta;
  if(cart[id]<=0) delete cart[id];
  render();
}
function updateCartBar(){
  const count = Object.values(cart).reduce((a,b)=>a+b,0);
  const total = Object.entries(cart).reduce((s,[id,qty])=>{
    const p=products.find(x=>x.id==id); return s + p.price*qty;
  },0);
  const box=document.getElementById("cartBox");
  if(count>0){
    box.classList.remove("hidden"); box.classList.add("flex");
    document.getElementById("cartCount").textContent=count;
    document.getElementById("cartTotal").textContent=formatRp(total);
  } else {
    box.classList.add("hidden"); box.classList.remove("flex");
  }
}
async function simpanKeDB(nama, hp, alamat, catatan){
  const items = Object.entries(cart).map(([id, qty])=>({produk_id: parseInt(id), qty}));
  if(items.length===0) return;
  try{
    const res = await fetch('/api/pesanan', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({nama: nama||'Pelanggan WA', hp: hp||'', alamat: alamat||'', items, metode_bayar:'WA', catatan: catatan||''})
    });
    const j = await res.json();
    console.log('Simpan DB:', j);
  }catch(e){ console.error('Gagal simpan DB', e); }
}

async function checkoutWA(){
  let lines = ["Halo Tysa Dessert, saya mau pesan:"];
  let total=0;
  for(const [id,qty] of Object.entries(cart)){
    const p=products.find(x=>x.id==id);
    lines.push(`- ${p.name} x${qty} = ${formatRp(p.price*qty)}`);
    total+=p.price*qty;
  }
  lines.push(`Total: ${formatRp(total)}`);
  lines.push("Alamat antar:");
  // Simpan ke database untuk rekap laporan (jangan blokir WA)
  const nama = prompt("Nama Anda untuk rekap pesanan (opsional, Enter untuk lewati):") || "Pelanggan WA";
  const hp = nama !== "Pelanggan WA" ? prompt("No HP (opsional):") || "" : "";
  if(Object.keys(cart).length>0){
    await simpanKeDB(nama, hp, "", lines.join("\n"));
  }
  const url=`https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(lines.join("\n"))}`;
  window.open(url,"_blank");
}
function pesanSatuan(id){
  const p=products.find(x=>x.id==id);
  const text=`Halo Tysa Dessert, saya mau pesan ${p.name} - ${formatRp(p.price)}. Apakah ready hari ini?`;
  window.open(`https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(text)}`,"_blank");
}
function kirimPesan(e){
  e.preventDefault();
  const nama=document.getElementById("nama").value;
  const pesan=document.getElementById("pesan").value;
  const hp=document.getElementById("hp").value;
  const full = `Halo Tysa Dessert, saya ${nama}${hp?" ("+hp+")":""}\n${pesan}`;
  window.open(`https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(full)}`,"_blank");
}

document.querySelectorAll("#filterBtns button").forEach(btn=>{
  btn.addEventListener("click",()=>{
    document.querySelectorAll("#filterBtns button").forEach(b=>{b.className="bg-white border px-4 py-2 rounded-full text-sm hover:bg-gray-50"});
    btn.className="bg-secondary text-white px-4 py-2 rounded-full text-sm";
    currentFilter=btn.dataset.filter;
    render();
  });
});

document.getElementById("btnMenu").addEventListener("click",()=>{
  document.getElementById("mobileNav").classList.toggle("hidden");
});

render();
