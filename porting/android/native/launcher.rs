//! Small JNI bridge to the exported launch API of the pinned Android runtime.
#![no_std]
use core::{ffi::c_void, ptr};

#[link(name = "dl")]
unsafe extern "C" {
    fn dlopen(name: *const u8, flags: i32) -> *mut c_void;
    fn dlsym(handle: *mut c_void, name: *const u8) -> *mut c_void;
}
#[link(name = "c")]
unsafe extern "C" {
    fn malloc(size: usize) -> *mut c_void;
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { loop {} }

// Runs on the Cocos GL thread after the runtime has created its main scene.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_org_ginka_launcher_GameActivity_nativeStartup(
    env: *mut *const *const c_void,
    _object: *mut c_void,
    path: *mut c_void,
) -> i32 {
    unsafe {
        let table = *env;
        // JNI slot offsets are checked against the JDK's JNINativeInterface_.
        let get: unsafe extern "system" fn(*mut *const *const c_void, *mut c_void, *mut u8) -> *const u8 = core::mem::transmute(*table.add(169));
        let release: unsafe extern "system" fn(*mut *const *const c_void, *mut c_void, *const u8) = core::mem::transmute(*table.add(170));
        let text = get(env, path, ptr::null_mut());
        if text.is_null() { return 1; }
        let mut len = 0;
        while *text.add(len) != 0 && len < 4096 { len += 1; }
        if len == 4096 { release(env, path, text); return 2; }
        let library = dlopen(c"libkrkr2.so".as_ptr().cast(), 2);
        if library.is_null() { release(env, path, text); return 3; }
        let get_scene = dlsym(library, c"_ZN12TVPMainScene11GetInstanceEv".as_ptr().cast());
        let startup = dlsym(library, c"_ZN12TVPMainScene11startupFromERKSs".as_ptr().cast());
        if get_scene.is_null() || startup.is_null() { release(env, path, text); return 4; }
        let instance: unsafe extern "C" fn() -> *mut c_void = core::mem::transmute(get_scene);
        let scene = instance();
        if scene.is_null() { release(env, path, text); return 5; }

        // The pinned runtime exports the old GNU std::string ABI (ERKSs).
        // Its shared representation has length, capacity and a reference count.
        // Keep one reference for the process lifetime while engine callbacks copy it.
        let header = 3 * core::mem::size_of::<usize>();
        let allocation = malloc(header + len + 1).cast::<u8>();
        if allocation.is_null() { release(env, path, text); return 6; }
        allocation.cast::<usize>().write(len);
        allocation.add(core::mem::size_of::<usize>()).cast::<usize>().write(len);
        allocation.add(2 * core::mem::size_of::<usize>()).cast::<i32>().write(0);
        let chars = allocation.add(header);
        ptr::copy_nonoverlapping(text, chars, len + 1);
        release(env, path, text);
        let launch: unsafe extern "C" fn(*mut c_void, *const *mut u8) -> bool = core::mem::transmute(startup);
        if launch(scene, &chars) { 0 } else { 7 }
    }
}
