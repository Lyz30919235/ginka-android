//! Converts PackinOne UI data to equivalent TJS data expressions.
use cxdec_tools::r#struct::pbd::{Pbd, PbdValue};
use std::{error::Error, fmt::Write, fs, io::Read, path::Path};

// Quotes strings without changing their contents or allowing script injection.
fn quote(value: &str) -> String {
    let mut out = String::from("\"");
    for ch in value.chars() {
        match ch {
            '\\' => out.push_str("\\\\"),
            '"' => out.push_str("\\\""),
            ch if ch.is_control() => {
                write!(out, "\\x{:04x}", ch as u32).unwrap();
            }
            ch => out.push(ch),
        }
    }
    out.push('"');
    out
}

// Serializes every supported value with its original type preserved.
fn expression(value: &PbdValue) -> Result<String, Box<dyn Error>> {
    Ok(match value {
        PbdValue::Null => "void".into(),
        PbdValue::ObjectNull => "null".into(),
        PbdValue::String(s) => quote(s),
        PbdValue::Bytes(b) => format!(
            "<% {} %>",
            b.iter()
                .map(|x| format!("{x:02x}"))
                .collect::<Vec<_>>()
                .join(" ")
        ),
        PbdValue::Integer(i) => i.to_string(),
        PbdValue::Real(f) if f.is_finite() => format!("real({})", f),
        PbdValue::Real(_) => return Err("non-finite PBD real value".into()),
        PbdValue::Array(a) => format!(
            "[{}]",
            a.iter()
                .map(expression)
                .collect::<Result<Vec<_>, _>>()?
                .join(",")
        ),
        PbdValue::Dictionary(d) => format!(
            "%[{}]",
            d.iter()
                .map(|(k, v)| Ok(format!("{} => {}", quote(k), expression(v)?)))
                .collect::<Result<Vec<_>, Box<dyn Error>>>()?
                .join(",")
        ),
    })
}

// Visits only PBD files and writes data expressions to a separate output tree.
fn convert_tree(input: &Path, output: &Path, relative: &Path) -> Result<usize, Box<dyn Error>> {
    let mut count = 0;
    for item in fs::read_dir(input.join(relative))? {
        let item = item?;
        let rel = relative.join(item.file_name());
        if item.file_type()?.is_dir() {
            count += convert_tree(input, output, &rel)?;
        } else if item.file_type()?.is_file() {
            let mut header = [0; 8];
            let mut file = fs::File::open(item.path())?;
            if file.read(&mut header)? < 8
                || !(header.starts_with(b"TJS/") || header.starts_with(b"TJS\\"))
                || !matches!(header[4], b'4' | b'n')
                || &header[5..8] != b"s0\0"
            {
                continue;
            }
            let parsed = Pbd::parse(&fs::read(item.path())?)?;
            let mut filename = rel.as_os_str().to_os_string();
            filename.push(".tjs");
            let target = output.join(filename);
            fs::create_dir_all(target.parent().unwrap())?;
            let text = format!("({})", expression(&parsed.root)?);
            let mut bytes = vec![0xff, 0xfe];
            for unit in text.encode_utf16() {
                bytes.extend_from_slice(&unit.to_le_bytes());
            }
            fs::write(target, bytes)?;
            count += 1;
        }
    }
    Ok(count)
}

// Runs an explicitly scoped conversion without deleting or overwriting inputs.
fn main() -> Result<(), Box<dyn Error>> {
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    if args.len() != 2 {
        return Err("usage: ginka-pbd-adapter INPUT OUTPUT".into());
    }
    let input = Path::new(&args[0]).canonicalize()?;
    let output = std::path::absolute(Path::new(&args[1]))?;
    if output.starts_with(&input) || input.starts_with(&output) {
        return Err("input and output must be separate trees".into());
    }
    println!(
        "converted_pbd_files={}",
        convert_tree(&input, &output, Path::new(""))?
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // Prevents executable text from escaping string and dictionary values.
    #[test]
    fn preserves_types_and_escapes_strings() {
        assert_eq!(quote("\"\\\n"), "\"\\\"\\\\\\x000a\"");
        assert_eq!(
            expression(&PbdValue::Array(vec![
                PbdValue::Null,
                PbdValue::ObjectNull,
                PbdValue::Integer(7)
            ]))
            .unwrap(),
            "[void,null,7]"
        );
        assert_eq!(
            expression(&PbdValue::Bytes(vec![0, 255])).unwrap(),
            "<% 00 ff %>"
        );
        assert!(expression(&PbdValue::Real(f64::NAN)).is_err());
    }
}
