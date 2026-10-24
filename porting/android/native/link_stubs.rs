//! Link-time import stubs only; these files must never be packaged in the APK.
#![no_std]
use core::ffi::c_void;
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { loop {} }
#[unsafe(no_mangle)]
#[cfg(dl_stub)]
pub extern "C" fn dlopen(_: *const u8, _: i32) -> *mut c_void { core::ptr::null_mut() }
#[unsafe(no_mangle)]
#[cfg(dl_stub)]
pub extern "C" fn dlsym(_: *mut c_void, _: *const u8) -> *mut c_void { core::ptr::null_mut() }
#[unsafe(no_mangle)]
#[cfg(c_stub)]
pub extern "C" fn malloc(_: usize) -> *mut c_void { core::ptr::null_mut() }
